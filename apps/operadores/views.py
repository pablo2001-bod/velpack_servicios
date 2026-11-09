from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.produccion.labels import preparar_etiquetas
from apps.produccion.models import (
    CronogramaDiario,
    DetalleProduccion,
    Operador,
    Paca,
    Produccion,
)
from apps.produccion.services import (
    generar_pacas,
    inicio_dia_operativo,
    obtener_turno_actual,
    turno_en_curso,
)

# Colores aproximados para la interfaz táctil.
COLORES_INTERFAZ = {
    "amarillo": "#f2c200",
    "verde": "#2e7d32",
    "gris": "#6b7280",
    "natural": "#c8a97e",
    "morado": "#7c3aed",
    "palo de rosa": "#e07a9a",
}


def _color_hex(color):
    return COLORES_INTERFAZ.get(color.nombre.strip().lower(), "#2e7d32")


def login_operador(request):
    """Permite al operador iniciar sesión ingresando su cédula o código de acceso."""
    if request.method == "POST":
        operador = Operador.buscar_por_credencial(request.POST.get("cedula"))

        if not operador:
            messages.error(
                request,
                "Credencial no encontrada o el operador se encuentra inactivo.",
            )
            return redirect("operadores:login_operador")

        request.session["operador_id"] = operador.id
        request.session["operador_nombre"] = operador.nombre_completo
        # Se limpia el estado previo para forzar la selección al iniciar sesión.
        request.session.pop("color_id", None)
        request.session.pop("etiquetas_rango", None)

        return redirect("operadores:terminal_operador")

    return render(request, "login_operadores/login_operador.html")


def terminal_operador(request):
    """Terminal táctil: registra producción y genera etiquetas con lote y QR."""
    operador_id = request.session.get("operador_id")
    if not operador_id:
        return redirect("operadores:login_operador")

    operador = get_object_or_404(Operador, id=operador_id)
    hoy = timezone.localdate()
    turno_actual = obtener_turno_actual()
    turno_actual_en_curso = turno_en_curso()

    cronograma_ids = list(
        CronogramaDiario.objects.filter(fecha=hoy, activo=True).values_list(
            "producto_id", flat=True
        )
    )

    productos = Producto.objects.filter(activo=True)
    if cronograma_ids:
        productos = productos.filter(
            Q(id__in=cronograma_ids) | Q(nombre__icontains="segunda")
        )
    productos = productos.distinct().order_by("nombre")

    colores = list(Color.objects.filter(activo=True).order_by("nombre"))
    for color in colores:
        color.hex_color = _color_hex(color)

    if request.method == "POST":
        accion = request.POST.get("accion", "registrar")

        if accion == "configurar_color":
            color_id = request.POST.get("color_id")
            if color_id and Color.objects.filter(id=color_id, activo=True).exists():
                request.session["color_id"] = color_id
                messages.success(request, "Color de trabajo configurado correctamente.")
            else:
                messages.error(request, "El color seleccionado no es válido.")
            return redirect("operadores:terminal_operador")

        if accion == "registrar_observacion":
            if not turno_actual:
                messages.error(request, "No hay un turno activo configurado.")
                return redirect("operadores:terminal_operador")

            observacion = request.POST.get("observacion", "").strip()
            if not observacion:
                messages.error(request, "Escribe una observación antes de enviarla.")
                return redirect("operadores:terminal_operador")

            with transaction.atomic():
                produccion, _ = Produccion.objects.get_or_create(
                    fecha=hoy,
                    operador=operador,
                    turno=turno_actual,
                    defaults={"observacion": ""},
                )
                nota = (
                    f"[{timezone.localtime():%d/%m/%Y %H:%M}] "
                    f"{operador.nombre_completo}: {observacion}"
                )
                produccion.observacion = (
                    f"{produccion.observacion}\n{nota}"
                    if produccion.observacion
                    else nota
                )
                produccion.save(update_fields=["observacion"])

            messages.success(request, "Observación enviada al administrador.")
            return redirect("operadores:terminal_operador")

        color_id = request.session.get("color_id")
        if not color_id:
            messages.error(request, "Por favor seleccione el color de trabajo.")
            return redirect("operadores:terminal_operador")

        if not turno_actual:
            messages.error(request, "No hay un turno activo configurado.")
            return redirect("operadores:terminal_operador")

        producto_id = request.POST.get("producto_id")
        try:
            cantidad = int(request.POST.get("cantidad_pacas", "1"))
        except (TypeError, ValueError):
            cantidad = 1

        if not producto_id or cantidad <= 0:
            messages.error(request, "Seleccione un modelo y una cantidad válida.")
            return redirect("operadores:terminal_operador")

        producto = get_object_or_404(Producto, id=producto_id)
        color = get_object_or_404(Color, id=color_id, activo=True)

        with transaction.atomic():
            produccion, _ = Produccion.objects.get_or_create(
                fecha=hoy,
                operador=operador,
                turno=turno_actual,
                defaults={
                    "observacion": "Registrado por lote desde Terminal Táctil"
                },
            )
            detalle, _ = DetalleProduccion.objects.get_or_create(
                produccion=produccion,
                producto=producto,
                color=color,
                defaults={"cantidad_pacas": 0},
            )
            detalle.cantidad_pacas += cantidad
            detalle.save()
            pacas = generar_pacas(detalle, cantidad)

        if pacas:
            # Rango compacto en sesión: evita guardar cientos de IDs.
            request.session["etiquetas_rango"] = {
                "detalle_id": detalle.id,
                "desde": pacas[0].numero_paca,
                "hasta": pacas[-1].numero_paca,
            }
            lotes = sorted({paca.lote for paca in pacas})
            detalle_lotes = ", ".join(f"L{n:02d}" for n in lotes)
            messages.success(
                request,
                f"Se registraron {cantidad} pacas de {producto.nombre} "
                f"({color.nombre}) en {detalle_lotes}.",
            )
            request.session["imprimir_ahora"] = True
            return redirect("operadores:terminal_operador")

        messages.error(request, "No se pudo generar la producción.")
        return redirect("operadores:terminal_operador")

    color_actual_id = request.session.get("color_id")
    color_actual = (
        Color.objects.filter(id=color_actual_id, activo=True).first()
        if color_actual_id
        else None
    )
    if color_actual:
        color_actual.hex_color = _color_hex(color_actual)

    pacas_hoy = Paca.objects.filter(
        detalle__produccion__operador=operador,
        fecha_creacion__gte=inicio_dia_operativo(),
    )
    pacas_color_hoy = (
        pacas_hoy.filter(detalle__color=color_actual).count() if color_actual else 0
    )
    ultima_paca = pacas_hoy.select_related("detalle").order_by("-fecha_creacion").first()

    context = {
        "operador_nombre": operador.nombre_completo,
        "turno_actual": turno_actual,
        "colores": colores,
        "productos": productos,
        "color_actual": color_actual,
        "necesita_config": not color_actual,
        "fecha_hoy": hoy,
        "pacas_hoy": pacas_hoy.count(),
        "pacas_color_hoy": pacas_color_hoy,
        "ultima_paca": ultima_paca,
        "turno_en_curso": turno_actual_en_curso,
        "puede_cerrar_sesion": turno_actual_en_curso is None,
        "imprimir_ahora": request.session.pop("imprimir_ahora", False),
    }
    return render(request, "login_operadores/terminal_operador.html", context)


def etiquetas_operador(request):
    """Etiquetas recién generadas o todas las del día para el operador."""
    operador_id = request.session.get("operador_id")
    if not operador_id:
        return redirect("operadores:login_operador")

    operador = get_object_or_404(Operador, id=operador_id)
    rango = request.session.get("etiquetas_rango")
    ver_todas = request.GET.get("todas") == "1"

    pacas_qs = Paca.objects.select_related(
        "detalle__producto",
        "detalle__color",
        "detalle__produccion__operador",
    ).filter(detalle__produccion__operador=operador)

    rango_valido = isinstance(rango, dict) and all(
        clave in rango for clave in ("detalle_id", "desde", "hasta")
    )

    if ver_todas or not rango_valido:
        pacas_qs = pacas_qs.filter(fecha_creacion__gte=inicio_dia_operativo())
        subtitulo = f"Etiquetas de hoy · {operador.nombre_completo}"
    else:
        pacas_qs = pacas_qs.filter(
            detalle_id=rango["detalle_id"],
            numero_paca__gte=rango["desde"],
            numero_paca__lte=rango["hasta"],
        )
        subtitulo = (
            f"Etiquetas generadas · {operador.nombre_completo} · "
            f"pacas {rango['desde']} a {rango['hasta']}"
        )

    pacas = list(
        pacas_qs.order_by(
            "detalle__producto__nombre",
            "detalle__color__nombre",
            "numero_paca",
        )
    )
    preparar_etiquetas(pacas, base_url=request.build_absolute_uri("/"))

    return render(
        request,
        "produccion/etiquetas.html",
        {
            "pacas": pacas,
            "titulo": "de producción",
            "subtitulo": subtitulo,
            "volver_url": reverse("operadores:terminal_operador"),
            "volver_texto": "Volver a la terminal",
        },
    )


def logout_operador(request):
    turno = turno_en_curso()
    if turno:
        messages.error(
            request,
            "No puedes cerrar sesión hasta que termine el turno "
            f"{turno.nombre} ({turno.hora_fin.strftime('%H:%M')}).",
        )
        return redirect("operadores:terminal_operador")

    request.session.flush()
    return redirect("operadores:login_operador")
