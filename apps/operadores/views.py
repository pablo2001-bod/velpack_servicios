from datetime import datetime, timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import AvisoInterno
from apps.catalogos.models import Color, Producto
from apps.produccion.labels import preparar_etiquetas
from apps.produccion.models import (
    ConfiguracionProduccion,
    CronogramaDiario,
    Operador,
    Paca,
    Produccion,
    Turno,
)
from apps.produccion.pdf import generar_archivo_pdf
from apps.produccion.services import (
    inicio_dia_operativo,
    limite_sesion,
    registrar_pacas,
    turno_para_inicio,
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


def _guardar_turno_en_sesion(request, turno, momento=None):
    request.session["turno_id"] = turno.id
    request.session["turno_limite"] = limite_sesion(turno, momento).isoformat()


def _turno_de_sesion(request, momento=None, crear=False):
    momento = momento or timezone.now()
    turno_id = request.session.get("turno_id")
    turno = None
    if turno_id:
        turno = Turno.objects.filter(id=turno_id, activo=True).first()
    if turno is None and crear:
        turno = turno_para_inicio(momento)
        if turno:
            _guardar_turno_en_sesion(request, turno, momento)
    return turno


def _limite_de_sesion(request):
    turno_id = request.session.get("turno_id")
    valor = request.session.get("turno_limite")
    if not turno_id:
        turno = turno_para_inicio()
        if turno:
            _guardar_turno_en_sesion(request, turno)
            turno_id = turno.id
    if not valor and turno_id:
        turno = Turno.objects.filter(id=turno_id, activo=True).first()
        if turno:
            valor = limite_sesion(turno).isoformat()
            request.session["turno_limite"] = valor
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def _sesion_expirada(request):
    if not request.session.get("operador_id"):
        return False
    limite = _limite_de_sesion(request)
    if limite and timezone.now() >= limite:
        request.session.flush()
        messages.info(
            request,
            "El turno terminó y la sesión se cerró automáticamente.",
        )
        return True
    return False


def login_operador(request):
    """Inicia sesión con cédula/código dentro de la ventana del turno."""
    if request.method == "POST":
        operador = Operador.buscar_por_credencial(request.POST.get("cedula"))

        if not operador:
            messages.error(
                request,
                "Credencial no encontrada o el operador se encuentra inactivo.",
            )
            return redirect("operadores:login_operador")

        turno = turno_para_inicio()
        if not turno:
            messages.error(
                request,
                "No puedes iniciar sesión fuera de la ventana de tu turno "
                "(10 minutos antes o después de la hora establecida).",
            )
            return redirect("operadores:login_operador")

        request.session["operador_id"] = operador.id
        request.session["operador_nombre"] = operador.nombre_completo
        _guardar_turno_en_sesion(request, turno)
        # Se limpia el estado previo para forzar la selección al iniciar sesión.
        request.session.pop("color_id", None)
        request.session.pop("etiquetas_rango", None)

        AvisoInterno.objects.create(
            tipo="ingreso_operador",
            titulo=f"Ingreso de operador: {operador.nombre_completo}",
            mensaje=(
                f"{operador.nombre_completo} inició turno '{turno.nombre}' el "
                f"{timezone.localtime():%d/%m/%Y a las %H:%M}."
            ),
            operador=operador,
        )

        return redirect("operadores:terminal_operador")

    return render(request, "login_operadores/login_operador.html")


def terminal_operador(request):
    """Terminal táctil: registra producción y genera etiquetas con lote y QR."""
    operador_id = request.session.get("operador_id")
    if not operador_id:
        return redirect("operadores:login_operador")
    if _sesion_expirada(request):
        return redirect("operadores:login_operador")

    operador = get_object_or_404(Operador, id=operador_id)
    hoy = timezone.localdate()
    turno_actual = _turno_de_sesion(request, crear=True)
    limite = _limite_de_sesion(request)
    puede_cerrar_sesion = limite is None or timezone.now() >= limite
    cierre_automatico_en = (
        max(0, int((limite - timezone.now()).total_seconds())) if limite else 0
    )

    cronograma_ids = list(
        CronogramaDiario.objects.filter(fecha=hoy, activo=True).values_list(
            "producto_id", flat=True
        )
    )

    productos = Producto.objects.filter(activo=True)
    if cronograma_ids:
        productos = productos.filter(
            Q(id__in=cronograma_ids) | Q(es_segunda=True)
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
                messages.info(request, "Sin novedades: no hay mensajes que registrar.")
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
                defaults={"observacion": ""},
            )
            detalle, pacas = registrar_pacas(produccion, producto, color, cantidad)

        if pacas:
            archivo_pdf = generar_archivo_pdf(
                pacas,
                f"Etiquetas terminal · {operador.nombre_completo}",
                produccion=produccion,
                base_url=request.build_absolute_uri("/"),
            )
            request.session["ultimo_pdf_id"] = archivo_pdf.id
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
        "turno_en_curso": turno_actual if not puede_cerrar_sesion else None,
        "puede_cerrar_sesion": puede_cerrar_sesion,
        "cierre_automatico_en": cierre_automatico_en,
        "pacas_por_lote": ConfiguracionProduccion.obtener().pacas_por_lote,
        "ultimo_pdf_id": request.session.get("ultimo_pdf_id"),
        "imprimir_ahora": request.session.pop("imprimir_ahora", False),
    }
    return render(request, "login_operadores/terminal_operador.html", context)


def etiquetas_operador(request):
    """Etiquetas recién generadas o todas las del día para el operador."""
    operador_id = request.session.get("operador_id")
    if not operador_id:
        return redirect("operadores:login_operador")
    if _sesion_expirada(request):
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
    limite = _limite_de_sesion(request)
    turno = _turno_de_sesion(request)
    if limite and timezone.now() < limite:
        fin = limite - timedelta(minutes=10)
        messages.error(
            request,
            "No puedes cerrar sesión hasta 10 minutos después del fin del turno "
            f"{turno.nombre if turno else ''} ({fin:%H:%M}).",
        )
        return redirect("operadores:terminal_operador")

    request.session.flush()
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("operadores:login_operador")
