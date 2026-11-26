"""Reglas de negocio compartidas del módulo de producción."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.proveedores.models import IngresoMateriaPrima

from .models import (
    ConsumoMateriaPrima,
    ConfiguracionProduccion,
    DetalleProduccion,
    Paca,
    ParametroProduccion,
    Turno,
)

# El día operativo arranca a las 06:00 y no a la medianoche.
HORA_CORTE = time(6, 0)
PACAS_POR_LOTE_POR_DEFECTO = 28
MARGEN_TURNO_MINUTOS = 10


def obtener_pacas_por_lote():
    """Tamaño de lote configurado desde la parte administrativa."""
    return ConfiguracionProduccion.obtener().pacas_por_lote


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


def _minutos(hora):
    return hora.hour * 60 + hora.minute + hora.second / 60


def _desde(desde, hora):
    """Minutos transcurridos entre dos horas, considerando medianoche."""
    return (_minutos(hora) - _minutos(desde)) % 1440


def _turno_en_franja(turno, hora):
    if turno.hora_inicio <= turno.hora_fin:
        return turno.hora_inicio <= hora < turno.hora_fin
    return hora >= turno.hora_inicio or hora < turno.hora_fin


def turno_para_inicio(momento=None):
    """Turno con el que debe iniciar sesión un operador.

    Se permite el margen de ``MARGEN_TURNO_MINUTOS`` antes del inicio y después
    del fin. Si dos turnos se solapan por el margen, gana el que está por
    empezar y luego el que está en curso.
    """
    momento = momento or timezone.now()
    hora = timezone.localtime(momento).time() if timezone.is_aware(momento) else momento.time()
    turnos = list(Turno.objects.filter(activo=True))

    por_empezar = [
        turno
        for turno in turnos
        if 0 < _desde(hora, turno.hora_inicio) <= MARGEN_TURNO_MINUTOS
    ]
    if por_empezar:
        return min(por_empezar, key=lambda turno: _desde(hora, turno.hora_inicio))

    en_curso = [turno for turno in turnos if _turno_en_franja(turno, hora)]
    if en_curso:
        return min(en_curso, key=lambda turno: _desde(hora, turno.hora_fin))

    recien_terminados = [
        turno
        for turno in turnos
        if 0 < _desde(turno.hora_fin, hora) <= MARGEN_TURNO_MINUTOS
    ]
    if recien_terminados:
        return max(recien_terminados, key=lambda turno: _desde(turno.hora_fin, hora))

    return None


def limite_sesion(turno, momento=None):
    """Momento en el que se cierra automáticamente la sesión del operador."""
    momento = momento or timezone.now()
    local = timezone.localtime(momento)
    inicio = datetime.combine(local.date(), turno.hora_inicio, tzinfo=local.tzinfo)
    fin = datetime.combine(local.date(), turno.hora_fin, tzinfo=local.tzinfo)
    if fin <= inicio:
        fin += timedelta(days=1)
    if local > fin + timedelta(minutes=MARGEN_TURNO_MINUTOS):
        fin += timedelta(days=1)
    return fin + timedelta(minutes=MARGEN_TURNO_MINUTOS)


def _codigo_producto_color(producto, color):
    return f"{producto.codigo.strip().upper()}{color.codigo.strip().upper()}"


def generar_pacas(detalle, cantidad):
    """Crea ``cantidad`` pacas consecutivas para un detalle de producción.

    La numeración es global por producto/color dentro del día operativo y el
    lote se calcula con el tamaño configurado desde la administración.
    """
    if cantidad <= 0:
        return []

    pacas_por_lote = obtener_pacas_por_lote()
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
            num_lote = ((numero_paca - 1) // pacas_por_lote) + 1
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


def _sumar_decimales(valores):
    return sum(valores, Decimal("0"))


def _etiqueta_insumo(tipo_material):
    return dict(IngresoMateriaPrima.TIPOS).get(tipo_material, tipo_material)


def _total_ingresado(tipo_material, bloquear=False):
    consulta = IngresoMateriaPrima.objects.filter(tipo_material=tipo_material)
    if bloquear:
        consulta = consulta.select_for_update()
    return _sumar_decimales(
        consulta.values_list("peso_neto", flat=True)
    )


def _total_consumido(tipo_material, bloquear=False):
    consulta = ConsumoMateriaPrima.objects.filter(tipo_material=tipo_material)
    if bloquear:
        consulta = consulta.select_for_update()
    return _sumar_decimales(
        consulta.values_list("cantidad_kg", flat=True)
    )


def obtener_stock_materia_prima():
    """Devuelve ingresos, consumos y saldo disponible por tipo de insumo."""
    ingresos = {
        item["tipo_material"]: item["total"] or Decimal("0")
        for item in IngresoMateriaPrima.objects.values("tipo_material")
        .annotate(total=Sum("peso_neto"))
    }
    consumos = {
        item["tipo_material"]: item["total"] or Decimal("0")
        for item in ConsumoMateriaPrima.objects.values("tipo_material")
        .annotate(total=Sum("cantidad_kg"))
    }

    tipos = sorted(set(ingresos) | set(consumos))
    return [
        {
            "tipo_material": tipo,
            "etiqueta": _etiqueta_insumo(tipo),
            "ingresado": ingresos.get(tipo, Decimal("0")),
            "consumido": consumos.get(tipo, Decimal("0")),
            "disponible": ingresos.get(tipo, Decimal("0"))
            - consumos.get(tipo, Decimal("0")),
        }
        for tipo in tipos
    ]


def descontar_materia_prima(detalle, cantidad_pacas):
    """Descuenta los insumos configurados para el color del detalle."""
    parametros = ParametroProduccion.objects.filter(
        color=detalle.color, activo=True
    )
    if not parametros or cantidad_pacas <= 0:
        return []

    requeridos = {}
    for parametro in parametros:
        requeridos[parametro.tipo_material] = (
            requeridos.get(parametro.tipo_material, Decimal("0"))
            + parametro.cantidad_por_paca * cantidad_pacas
        )

    consumos = []
    for tipo_material, cantidad_kg in requeridos.items():
        disponible = _total_ingresado(tipo_material, bloquear=True) - _total_consumido(
            tipo_material, bloquear=True
        )
        if disponible < cantidad_kg:
            raise ValueError(
                f"Stock insuficiente de {_etiqueta_insumo(tipo_material)}: "
                f"se requieren {cantidad_kg} kg y hay {disponible} kg disponibles."
            )
        consumos.append(
            ConsumoMateriaPrima(
                detalle=detalle,
                tipo_material=tipo_material,
                cantidad_kg=cantidad_kg,
            )
        )

    ConsumoMateriaPrima.objects.bulk_create(consumos)
    return consumos


def registrar_pacas(produccion, producto, color, cantidad):
    """Registra un lote de pacas y devuelve el detalle y las pacas creadas."""
    with transaction.atomic():
        detalle, _ = DetalleProduccion.objects.get_or_create(
            produccion=produccion,
            producto=producto,
            color=color,
            defaults={"cantidad_pacas": 0},
        )
        descontar_materia_prima(detalle, cantidad)
        detalle.cantidad_pacas += cantidad
        detalle.save()
        pacas = generar_pacas(detalle, cantidad)
    return detalle, pacas


def recalcular_lotes_y_codigos():
    """Recalcula lote y código de barras de las pacas al cambiar el lote."""
    pacas_por_lote = obtener_pacas_por_lote()
    pacas = list(Paca.objects.select_related(
        "detalle__produccion__operador", "detalle__producto", "detalle__color"
    ))
    for paca in pacas:
        paca.lote = ((paca.numero_paca - 1) // pacas_por_lote) + 1
        prefijo = paca.codigo_unico.rsplit("L", 1)[0]
        paca.codigo_unico = f"{prefijo}L{paca.lote:02d}"
    with transaction.atomic():
        Paca.objects.bulk_update(pacas, ["lote", "codigo_unico"])
    return len(pacas)
