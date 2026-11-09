"""Reglas de negocio compartidas del módulo de producción."""

from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from .models import Paca, Turno

# El día operativo arranca a las 06:00 y no a la medianoche.
HORA_CORTE = time(6, 0)
PACAS_POR_LOTE = 50


def inicio_dia_operativo(momento=None):
    """Devuelve el inicio del día operativo (06:00) que corresponde a ``momento``."""
    momento = momento or timezone.now()

    if timezone.is_aware(momento):
        local = timezone.localtime(momento)
    else:
        local = momento

    fecha = local.date()
    if local.time() < HORA_CORTE:
        fecha -= timedelta(days=1)

    inicio = datetime.combine(fecha, HORA_CORTE)
    if timezone.is_aware(momento):
        inicio = timezone.make_aware(inicio, local.tzinfo)
    return inicio


def obtener_turno_actual():
    """Turno activo que corresponde a la hora actual (soporta turnos nocturnos)."""
    hora_actual = timezone.localtime(timezone.now()).time()

    for turno in Turno.objects.filter(activo=True):
        if turno.hora_inicio <= turno.hora_fin:
            if turno.hora_inicio <= hora_actual <= turno.hora_fin:
                return turno
        elif hora_actual >= turno.hora_inicio or hora_actual <= turno.hora_fin:
            return turno

    return Turno.objects.filter(activo=True).first()


def turno_en_curso():
    """Devuelve el turno cuya franja horaria incluye la hora actual.

    A diferencia de ``obtener_turno_actual``, no devuelve un turno de respaldo
    cuando ya terminó la jornada. Se usa para bloquear el cierre de sesión del
    operador mientras su turno siga vigente.
    """
    hora_actual = timezone.localtime(timezone.now()).time()

    for turno in Turno.objects.filter(activo=True):
        if turno.hora_inicio <= turno.hora_fin:
            if turno.hora_inicio <= hora_actual < turno.hora_fin:
                return turno
        elif hora_actual >= turno.hora_inicio or hora_actual < turno.hora_fin:
            return turno

    return None


def _codigo_producto_color(producto, color):
    return f"{producto.codigo.strip().upper()}{color.codigo.strip().upper()}"


def generar_pacas(detalle, cantidad):
    """Crea ``cantidad`` pacas consecutivas para un detalle de producción.

    La numeración es global por producto/color dentro del día operativo, y el
    lote se calcula en bloques de 50 pacas.
    """
    if cantidad <= 0:
        return []

    produccion = detalle.produccion
    producto = detalle.producto
    color = detalle.color

    iniciales = produccion.operador.obtener_iniciales()
    fecha_formateada = produccion.fecha.strftime("%d%m%y")
    codigo_producto_color = _codigo_producto_color(producto, color)

    creadas = []
    with transaction.atomic():
        ultima_paca = (
            Paca.objects.select_for_update()
            .filter(
                detalle__producto=producto,
                detalle__color=color,
                fecha_creacion__gte=inicio_dia_operativo(),
            )
            .order_by("-numero_paca")
            .first()
        )
        total_previo = ultima_paca.numero_paca if ultima_paca else 0

        for i in range(1, cantidad + 1):
            numero_paca = total_previo + i
            num_lote = ((numero_paca - 1) // PACAS_POR_LOTE) + 1
            codigo_unico = (
                f"{iniciales}{fecha_formateada}{codigo_producto_color}"
                f"{numero_paca:03d}L{num_lote:02d}"
            )
            creadas.append(
                Paca.objects.create(
                    detalle=detalle,
                    numero_paca=numero_paca,
                    lote=num_lote,
                    codigo_unico=codigo_unico,
                )
            )

    return creadas
