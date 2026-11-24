from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.catalogos.models import Color, Producto

from .forms import (
    ColorForm,
    ConfiguracionProduccionForm,
    ItemsProduccionFormSet,
    ModeloForm,
    RegistroProduccionForm,
)
from .labels import preparar_etiquetas
from .models import (
    ArchivoEtiquetas,
    ConfiguracionProduccion,
    CronogramaDiario,
    Paca,
    Produccion,
)
from .pdf import generar_archivo_pdf
from .services import (
    registrar_pacas,
    turno_en_curso,
)


@login_required(login_url="/login/")
def lista_produccion(request):
    producciones = Produccion.objects.prefetch_related(
        "detalles__producto", "detalles__color"
    ).all()
    return render(request, "produccion/lista.html", {"producciones": producciones})


def _solo_admin(view):
    return user_passes_test(lambda u: u.is_superuser)(view)


@login_required(login_url="/login/")
def gestionar_cronograma(request):
    """Vista para seleccionar los modelos activos del día y gestionar catálogos."""
    hoy = timezone.localdate()
    productos = Producto.objects.all().order_by("nombre")
    colores = Color.objects.all().order_by("nombre")

    if request.method == "POST" and not request.user.is_superuser:
        messages.error(request, "Solo el administrador puede modificar el cronograma.")
        return redirect("produccion:registrar")

    if request.method == "POST":
        productos_ids = request.POST.getlist("productos_activos[]")
        # Solo se aceptan IDs de productos existentes.
        productos_ids = list(
            Producto.objects.filter(id__in=productos_ids).values_list("id", flat=True)
        )

        with transaction.atomic():
            # Se reemplaza el cronograma del día por la nueva selección.
            CronogramaDiario.objects.filter(fecha=hoy).delete()
            CronogramaDiario.objects.bulk_create(
                [
                    CronogramaDiario(fecha=hoy, producto_id=prod_id, activo=True)
                    for prod_id in productos_ids
                ],
                ignore_conflicts=True,
            )

        messages.success(request, "¡Cronograma de producción actualizado con éxito!")
        return redirect("produccion:registrar")

    productos_seleccionados_ids = list(
        CronogramaDiario.objects.filter(fecha=hoy, activo=True).values_list(
            "producto_id", flat=True
        )
    )

    return render(
        request,
        "produccion/cronograma.html",
        {
            "productos": productos,
            "colores": colores,
            "productos_seleccionados_ids": productos_seleccionados_ids,
            "fecha_hoy": hoy,
            "es_admin": request.user.is_superuser,
            "configuracion": ConfiguracionProduccion.obtener(),
            "form_configuracion": ConfiguracionProduccionForm(
                instance=ConfiguracionProduccion.obtener()
            ),
        },
    )


@_solo_admin
def crear_modelo(request):
    if request.method == "POST":
        form = ModeloForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Modelo agregado correctamente.")
            return redirect("produccion:registrar")
    else:
        form = ModeloForm()
    return render(
        request,
        "produccion/catalogo_form.html",
        {"form": form, "titulo": "Agregar modelo", "volver": "produccion:registrar"},
    )


@_solo_admin
def editar_modelo(request, pk):
    modelo = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        form = ModeloForm(request.POST, instance=modelo)
        if form.is_valid():
            form.save()
            messages.success(request, "Modelo actualizado correctamente.")
            return redirect("produccion:registrar")
    else:
        form = ModeloForm(instance=modelo)
    return render(
        request,
        "produccion/catalogo_form.html",
        {"form": form, "titulo": "Editar modelo", "volver": "produccion:registrar"},
    )


@_solo_admin
@require_POST
def eliminar_modelo(request, pk):
    modelo = get_object_or_404(Producto, pk=pk)
    try:
        modelo.delete()
    except ProtectedError:
        modelo.activo = False
        modelo.save(update_fields=["activo"])
        messages.warning(
            request,
            "El modelo tiene producción registrada: se desactivó en lugar de eliminarse.",
        )
    else:
        messages.success(request, "Modelo eliminado correctamente.")
    return redirect("produccion:registrar")


@_solo_admin
def crear_color(request):
    if request.method == "POST":
        form = ColorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Color agregado correctamente.")
            return redirect("produccion:registrar")
    else:
        form = ColorForm()
    return render(
        request,
        "produccion/catalogo_form.html",
        {"form": form, "titulo": "Agregar color", "volver": "produccion:registrar"},
    )


@_solo_admin
def editar_color(request, pk):
    color = get_object_or_404(Color, pk=pk)
    if request.method == "POST":
        form = ColorForm(request.POST, instance=color)
        if form.is_valid():
            form.save()
            messages.success(request, "Color actualizado correctamente.")
            return redirect("produccion:registrar")
    else:
        form = ColorForm(instance=color)
    return render(
        request,
        "produccion/catalogo_form.html",
        {"form": form, "titulo": "Editar color", "volver": "produccion:registrar"},
    )


@_solo_admin
@require_POST
def eliminar_color(request, pk):
    color = get_object_or_404(Color, pk=pk)
    try:
        color.delete()
    except ProtectedError:
        color.activo = False
        color.save(update_fields=["activo"])
        messages.warning(
            request,
            "El color tiene producción registrada: se desactivó en lugar de eliminarse.",
        )
    else:
        messages.success(request, "Color eliminado correctamente.")
    return redirect("produccion:registrar")


@_solo_admin
def configurar_produccion(request):
    configuracion = ConfiguracionProduccion.obtener()
    if request.method == "POST":
        form = ConfiguracionProduccionForm(request.POST, instance=configuracion)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Tamaño de lote actualizado. Los códigos y lotes se recalcularon.",
            )
            return redirect("produccion:registrar")
    else:
        form = ConfiguracionProduccionForm(instance=configuracion)
    return render(
        request,
        "produccion/configuracion.html",
        {"form": form, "configuracion": configuracion},
    )


@_solo_admin
def registrar_produccion_admin(request):
    if request.method == "POST":
        form = RegistroProduccionForm(request.POST)
        items = ItemsProduccionFormSet(request.POST, prefix="items")
        if form.is_valid() and items.is_valid():
            turno = turno_en_curso()
            if not turno:
                messages.error(request, "No hay un turno activo configurado.")
            else:
                datos = form.cleaned_data
                produccion, _ = Produccion.objects.get_or_create(
                    fecha=timezone.localdate(),
                    operador=datos["operador"],
                    turno=turno,
                    defaults={"observacion": datos["observacion"]},
                )
                pacas_totales = []
                for item in items.cleaned_data:
                    if item.get("DELETE"):
                        continue
                    _, pacas = registrar_pacas(
                        produccion,
                        item["producto"],
                        item["color"],
                        item["cantidad_pacas"],
                    )
                    pacas_totales.extend(pacas)
                generar_archivo_pdf(
                    pacas_totales,
                    f"Etiquetas producción #{produccion.id}",
                    produccion=produccion,
                    base_url=request.build_absolute_uri("/"),
                )
                messages.success(
                    request,
                    f"Se registraron {len(pacas_totales)} pacas y su PDF de etiquetas.",
                )
                return redirect("produccion:registrar")
    else:
        form = RegistroProduccionForm()
        items = ItemsProduccionFormSet(prefix="items")
    return render(
        request,
        "produccion/registrar_produccion.html",
        {"form": form, "items": items},
    )


def descargar_pdf(request, id):
    if not request.user.is_authenticated and not request.session.get("operador_id"):
        return redirect("login")

    archivo = get_object_or_404(ArchivoEtiquetas, id=id)
    nombre = archivo.archivo.name.rsplit("/", 1)[-1]
    return FileResponse(
        archivo.archivo.open("rb"),
        as_attachment=True,
        filename=nombre,
        content_type="application/pdf",
    )


@login_required(login_url="/login/")
def pdf_produccion(request, id):
    produccion = get_object_or_404(Produccion, id=id)
    pacas = list(
        Paca.objects.filter(detalle__produccion=produccion)
        .select_related(
            "detalle__producto",
            "detalle__color",
            "detalle__produccion__operador",
        )
        .order_by("numero_paca")
    )
    if not pacas:
        messages.error(request, "Esta producción todavía no tiene pacas registradas.")
        return redirect("produccion:detalle_produccion", id=id)

    archivo = generar_archivo_pdf(
        pacas,
        f"Etiquetas producción #{produccion.id}",
        produccion=produccion,
        base_url=request.build_absolute_uri("/"),
    )
    return redirect("produccion:descargar_pdf", id=archivo.id)


@login_required(login_url="/login/")
def detalle_produccion(request, id):
    produccion = get_object_or_404(
        Produccion.objects.prefetch_related(
            "detalles__producto", "detalles__color", "detalles__pacas"
        ),
        id=id,
    )
    return render(
        request,
        "produccion/detalle.html",
        {"produccion": produccion},
    )


@login_required(login_url="/login/")
def buscar_codigo(request):
    codigo = request.GET.get("codigo", "").strip()
    paca = None
    error_mensaje = None

    if codigo:
        try:
            paca = Paca.objects.select_related(
                "detalle__produccion",
                "detalle__producto",
                "detalle__color",
                "detalle__produccion__operador",
            ).get(codigo_unico__iexact=codigo)
        except Paca.DoesNotExist:
            error_mensaje = (
                f"No se encontró ninguna paca registrada con el código: '{codigo}'"
            )

    if paca:
        preparar_etiquetas([paca], base_url=request.build_absolute_uri("/"))

    return render(
        request,
        "produccion/buscar_codigo.html",
        {
            "paca": paca,
            "codigo": codigo,
            "error_mensaje": error_mensaje,
        },
    )


def ficha_paca(request, codigo):
    """Ficha pública de trazabilidad a la que apunta el QR de la etiqueta."""
    paca = get_object_or_404(
        Paca.objects.select_related(
            "detalle__produccion",
            "detalle__producto",
            "detalle__color",
            "detalle__produccion__operador",
            "detalle__produccion__turno",
        ),
        codigo_unico__iexact=codigo,
    )
    preparar_etiquetas([paca], base_url=request.build_absolute_uri("/"))
    return render(request, "produccion/ficha_paca.html", {"paca": paca})


@login_required(login_url="/login/")
def imprimir_etiquetas(request, id):
    """Vista de impresión de etiquetas para una producción completa."""
    produccion = get_object_or_404(
        Produccion.objects.select_related("operador", "turno"), id=id
    )
    pacas = list(
        Paca.objects.filter(detalle__produccion=produccion)
        .select_related(
            "detalle__producto",
            "detalle__color",
            "detalle__produccion__operador",
        )
        .order_by("detalle__producto__nombre", "detalle__color__nombre", "numero_paca")
    )
    preparar_etiquetas(pacas, base_url=request.build_absolute_uri("/"))

    return render(
        request,
        "produccion/etiquetas.html",
        {
            "pacas": pacas,
            "titulo": f"Producción #{produccion.id}",
            "subtitulo": (
                f"{produccion.operador.nombre_completo} · "
                f"{produccion.fecha:%d/%m/%Y} · {produccion.turno.nombre}"
            ),
            "volver_url": reverse(
                "produccion:detalle_produccion", args=[produccion.id]
            ),
            "volver_texto": "Volver al detalle",
            "pdf_url": reverse("produccion:pdf_produccion", args=[produccion.id]),
        },
    )
