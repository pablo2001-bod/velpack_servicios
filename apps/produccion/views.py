from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.catalogos.models import Producto

from .labels import preparar_etiquetas
from .models import CronogramaDiario, Paca, Produccion


@login_required(login_url="/login/")
def lista_produccion(request):
    producciones = Produccion.objects.prefetch_related(
        "detalles__producto", "detalles__color"
    ).all()
    return render(request, "produccion/lista.html", {"producciones": producciones})


@login_required(login_url="/login/")
def gestionar_cronograma(request):
    """Vista para que el administrador seleccione los modelos activos del día."""
    hoy = timezone.localdate()
    productos = Producto.objects.all()

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
            "productos_seleccionados_ids": productos_seleccionados_ids,
            "fecha_hoy": hoy,
        },
    )


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
        },
    )
