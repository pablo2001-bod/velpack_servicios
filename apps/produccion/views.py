from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.despachos.models import DetalleDespacho
from apps.proveedores.models import categoria_insumo
from apps.ventas.models import DetalleVenta

from .forms import (
    ColorForm,
    ConfiguracionProduccionForm,
    ItemsProduccionFormSet,
    ModeloForm,
    ParametroColorForm,
    ParametrosInsumosFormSet,
    RegistroProduccionForm,
)
from .labels import preparar_etiquetas
from .models import (
    ArchivoEtiquetas,
    ConfiguracionProduccion,
    CronogramaDiario,
    DetalleProduccion,
    Paca,
    ParametroProduccion,
    Produccion,
)
from .pdf import generar_archivo_pdf
from .services import (
    obtener_stock_materia_prima,
    registrar_pacas,
    turno_en_curso,
)


@login_required(login_url="/login/")
def lista_produccion(request):
    producciones = Produccion.objects.prefetch_related(
        "detalles__producto", "detalles__color"
    ).all()
    return render(
        request,
        "produccion/lista.html",
        {"producciones": producciones, "es_admin": request.user.is_superuser},
    )


def _solo_admin(view):
    return user_passes_test(lambda u: u.is_superuser)(view)


@never_cache
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
            "productos_economicos": Producto.objects.filter(es_segunda=True).order_by(
                "nombre"
            ),
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
    es_economico = modelo.es_segunda
    if request.method == "POST":
        form = ModeloForm(request.POST, instance=modelo)
        if form.is_valid():
            modelo_actualizado = form.save(commit=False)
            if es_economico:
                modelo_actualizado.es_segunda = True
                modelo_actualizado.activo = True
            modelo_actualizado.save()
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
    referencias = []
    if DetalleProduccion.objects.filter(color=color).exists():
        referencias.append("producción")
    if DetalleDespacho.objects.filter(color=color).exists():
        referencias.append("despachos")
    if DetalleVenta.objects.filter(color=color).exists():
        referencias.append("ventas")

    with transaction.atomic():
        ParametroProduccion.objects.filter(color=color).delete()
        if referencias:
            color.activo = False
            color.save(update_fields=["activo"])
            messages.warning(
                request,
                f"El color tiene registros de {', '.join(referencias)}: se desactivó.",
            )
        else:
            color.delete()
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


def _guardar_parametros_insumos(color, activo_color, formset):
    tipos = []
    with transaction.atomic():
        for fila in formset.cleaned_data:
            if fila.get("DELETE"):
                continue
            tipo = fila["tipo_material"]
            tipos.append(tipo)
            ParametroProduccion.objects.update_or_create(
                color=color,
                tipo_material=tipo,
                defaults={
                    "cantidad_por_paca": fila["cantidad_por_paca"],
                    "activo": activo_color and fila["activo"],
                },
            )
        ParametroProduccion.objects.filter(color=color).exclude(
            tipo_material__in=tipos
        ).delete()


@_solo_admin
def lista_parametros(request):
    parametros = list(
        ParametroProduccion.objects.select_related("color").all().order_by("color__nombre")
    )
    for parametro in parametros:
        parametro.categoria = categoria_insumo(parametro.tipo_material)
    return render(
        request,
        "produccion/parametros.html",
        {
            "parametros": parametros,
            "stock_materia_prima": obtener_stock_materia_prima(),
        },
    )


@_solo_admin
def crear_parametro(request):
    form = ParametroColorForm(request.POST or None)
    insumos = ParametrosInsumosFormSet(request.POST or None, prefix="insumos")
    if request.method == "POST" and form.is_valid() and insumos.is_valid():
        _guardar_parametros_insumos(
            form.cleaned_data["color"], form.cleaned_data["activo"], insumos
        )
        messages.success(request, "Parámetros de producción agregados correctamente.")
        return redirect("produccion:parametros")
    return render(
        request,
        "produccion/parametro_form.html",
        {
            "form": form,
            "insumos": insumos,
            "titulo": "Nuevo parámetro de producción",
            "volver": "produccion:parametros",
        },
    )


@_solo_admin
def editar_parametro(request, pk):
    parametro = get_object_or_404(ParametroProduccion, pk=pk)
    parametros = ParametroProduccion.objects.filter(color=parametro.color).order_by(
        "tipo_material"
    )
    initial = [
        {
            "tipo_material": item.tipo_material,
            "cantidad_por_paca": item.cantidad_por_paca,
            "activo": item.activo,
        }
        for item in parametros
    ]
    form = ParametroColorForm(
        request.POST or None,
        initial={
            "color": parametro.color,
            "activo": any(item.activo for item in parametros),
        },
    )
    form.fields["color"].disabled = True
    insumos = ParametrosInsumosFormSet(
        request.POST or None, initial=initial, prefix="insumos"
    )
    if request.method == "POST" and form.is_valid() and insumos.is_valid():
        _guardar_parametros_insumos(
            form.cleaned_data["color"], form.cleaned_data["activo"], insumos
        )
        messages.success(request, "Parámetros de producción actualizados correctamente.")
        return redirect("produccion:parametros")
    return render(
        request,
        "produccion/parametro_form.html",
        {
            "form": form,
            "insumos": insumos,
            "titulo": "Editar parámetros de producción",
            "volver": "produccion:parametros",
        },
    )


@_solo_admin
@require_POST
def eliminar_parametro(request, pk):
    parametro = get_object_or_404(ParametroProduccion, pk=pk)
    parametro.delete()
    messages.success(request, "Parámetro de producción eliminado correctamente.")
    return redirect("produccion:parametros")


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
                try:
                    with transaction.atomic():
                        for item in items.cleaned_data:
                            if item.get("DELETE") or not all(
                                item.get(campo)
                                for campo in ("producto", "color", "cantidad_pacas")
                            ):
                                continue
                            _, pacas = registrar_pacas(
                                produccion,
                                item["producto"],
                                item["color"],
                                item["cantidad_pacas"],
                            )
                            pacas_totales.extend(pacas)
                except ValueError as error:
                    messages.error(request, str(error))
                    return render(
                        request,
                        "produccion/registrar_produccion.html",
                        {"form": form, "items": items},
                    )
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


@_solo_admin
@require_POST
def eliminar_produccion(request, id):
    produccion = get_object_or_404(Produccion, id=id)
    produccion.delete()
    messages.success(request, "Producción eliminada correctamente.")
    return redirect("produccion:lista")


@_solo_admin
@require_POST
def eliminar_historial_produccion(request):
    cantidad = Produccion.objects.count()
    with transaction.atomic():
        Produccion.objects.all().delete()
    messages.success(request, f"Se eliminaron {cantidad} producciones.")
    return redirect("produccion:lista")


@login_required(login_url="/login/")
def descargar_pdf(request, id):
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
