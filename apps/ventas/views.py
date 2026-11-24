from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import PerfilUsuario
from apps.catalogos.models import Color, Producto

from .forms import VentaForm
from .models import DetalleVenta, Venta


@staff_member_required
def lista_ventas(request):
    ventas = Venta.objects.select_related("cliente").order_by("-id")

    query = request.GET.get("q", "").strip()
    if query:
        ventas = ventas.filter(
            Q(cliente__ruc__icontains=query)
            | Q(cliente__nombre__icontains=query)
            | Q(numero_factura__icontains=query)
        )

    return render(request, "ventas/lista_ventas.html", {"ventas": ventas, "query": query})


def _opciones_pago(request):
    metodo = request.POST.get("metodo_pago", "efectivo")
    estado = request.POST.get("estado_pago", "pagado")
    if metodo not in dict(Venta.METODO_PAGO_CHOICES) or estado not in dict(
        Venta.ESTADO_PAGO_CHOICES
    ):
        raise ValueError("El método o estado de pago seleccionado no es válido.")
    return metodo, estado


def _obtener_filas_detalle(request):
    """Extrae y valida las filas de detalle enviadas por el formulario."""
    modelos = request.POST.getlist("modelo[]")
    colores = request.POST.getlist("color[]")
    cantidades = request.POST.getlist("cantidad[]")
    precios = request.POST.getlist("precio[]")

    filas = []
    for i in range(len(modelos)):
        modelo_id = modelos[i]
        color_id = colores[i] if i < len(colores) else ""
        cantidad_raw = cantidades[i] if i < len(cantidades) else ""
        precio_raw = precios[i] if i < len(precios) else ""

        # Se ignoran las filas vacías que agrega dinámicamente el formulario.
        if not (modelo_id and color_id and cantidad_raw and precio_raw):
            continue

        try:
            modelo = Producto.objects.get(pk=modelo_id, activo=True)
            color = Color.objects.get(pk=color_id, activo=True)
            cantidad = int(cantidad_raw)
            precio = Decimal(str(precio_raw))
        except (
            Producto.DoesNotExist,
            Color.DoesNotExist,
            TypeError,
            ValueError,
            InvalidOperation,
        ):
            raise ValueError("Hay modelos, colores, cantidades o precios no válidos.")

        if cantidad <= 0:
            raise ValueError("La cantidad de pacas debe ser mayor a cero.")
        if precio < 0:
            raise ValueError("El precio unitario no puede ser negativo.")

        filas.append((modelo.id, color.id, cantidad, precio))

    return filas


@staff_member_required
def crear_venta(request):
    form = VentaForm(request.POST or None)

    if request.method == "POST":
        try:
            filas = _obtener_filas_detalle(request)
            metodo_pago, estado_pago = _opciones_pago(request)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("ventas:crear_venta")

        if not filas:
            messages.error(request, "Debe agregar al menos un producto a la venta.")
            return redirect("ventas:crear_venta")

        if not form.is_valid():
            messages.error(request, "Revise los datos de la factura.")
            return redirect("ventas:crear_venta")

        try:
            with transaction.atomic():
                venta = form.save(commit=False)
                venta.usuario = PerfilUsuario.obtener_o_crear_para(request.user)
                venta.metodo_pago = metodo_pago
                venta.estado_pago = estado_pago
                venta.observacion = request.POST.get("observacion", "").strip()
                venta.save()

                for modelo_id, color_id, cantidad, precio in filas:
                    DetalleVenta.objects.create(
                        venta=venta,
                        modelo_id=modelo_id,
                        color_id=color_id,
                        cantidad_pacas=cantidad,
                        precio_unitario=precio,
                        subtotal=precio * cantidad,
                    )
        except ValidationError as error:
            messages.error(request, f"Error de stock: {error.messages[0]}")
        except Exception:
            messages.error(request, "Ocurrió un error al registrar la venta.")
        else:
            messages.success(request, "Venta registrada exitosamente.")
            return redirect("ventas:lista_ventas")

        return redirect("ventas:crear_venta")

    return render(
        request,
        "ventas/form_venta.html",
        {
            "form": form,
            "modelos": Producto.objects.all(),
            "colores": Color.objects.all(),
        },
    )


@staff_member_required
@require_POST
def actualizar_estado_pago(request, pk):
    """Vista para actualizar el método y estado de pago desde la lista de ventas."""
    venta = get_object_or_404(Venta, pk=pk)

    if venta.estado_pago == "pagado":
        messages.error(
            request,
            f"La factura #{venta.numero_factura} ya está pagada y no se puede modificar.",
        )
        return redirect("ventas:lista_ventas")

    try:
        metodo_pago, estado_pago = _opciones_pago(request)
    except ValueError as error:
        messages.error(request, str(error))
        return redirect("ventas:lista_ventas")

    venta.metodo_pago = metodo_pago
    venta.estado_pago = estado_pago
    venta.save(update_fields=["metodo_pago", "estado_pago"])
    messages.success(
        request,
        f"Se actualizó el estado de la factura #{venta.numero_factura} correctamente.",
    )
    return redirect("ventas:lista_ventas")
