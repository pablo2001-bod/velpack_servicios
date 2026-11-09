from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.produccion.models import Paca
from apps.proveedores.models import IngresoMateriaPrima
from apps.ventas.models import DetalleVenta, Venta

# Color real de cada línea para el panel futurista de producción.
COLORES_PRODUCCION = {
    "amarillo": "#f2c200",
    "verde": "#2e7d32",
    "gris": "#6b7280",
    "natural": "#c8a97e",
    "morado": "#7c3aed",
    "palo de rosa": "#e07a9a",
}
COLOR_PRODUCCION_FALLBACK = "#22d3ee"


def _color_produccion(nombre):
    return COLORES_PRODUCCION.get(
        (nombre or "").strip().lower(), COLOR_PRODUCCION_FALLBACK
    )


@login_required
def dashboard_analiticas(request):
    """Panel de inteligencia calculado 100% a partir de los registros reales."""
    hoy = timezone.localdate()
    desde = hoy - timedelta(days=29)

    # Producción: pacas generadas por modelo y color.
    produccion_por_modelo = list(
        Paca.objects.values(
            "detalle__producto__nombre", "detalle__color__nombre"
        )
        .annotate(total=Count("id"))
        .order_by("-total", "detalle__producto__nombre")
    )
    for item in produccion_por_modelo:
        item["color_hex"] = _color_produccion(item["detalle__color__nombre"])

    # Productos más vendidos por cantidad e ingresos.
    productos_mas_vendidos = list(
        DetalleVenta.objects.values("modelo__nombre", "color__nombre")
        .annotate(
            cantidad_total=Sum("cantidad_pacas"),
            ingresos=Sum("subtotal"),
        )
        .order_by("-cantidad_total", "-ingresos")
    )

    # Clientes más activos: se ordenan por monto vendido y luego por compras.
    total_ingresos = Venta.objects.aggregate(total=Sum("total"))["total"] or 0
    clientes_activos = list(
        Venta.objects.values("cliente__id", "cliente__nombre", "cliente__ruc")
        .annotate(total_ventas=Sum("total"), compras=Count("id"))
        .order_by("-total_ventas", "-compras")[:5]
    )
    ids_clientes = [cliente["cliente__id"] for cliente in clientes_activos]
    pacas_por_cliente = {
        fila["venta__cliente_id"]: fila["total"] or 0
        for fila in DetalleVenta.objects.filter(
            venta__cliente_id__in=ids_clientes
        )
        .values("venta__cliente_id")
        .annotate(total=Sum("cantidad_pacas"))
    }
    for cliente in clientes_activos:
        cliente["total_pacas"] = pacas_por_cliente.get(cliente["cliente__id"], 0)
        cliente["porcentaje"] = (
            round(float(cliente["total_ventas"] or 0) / float(total_ingresos) * 100, 1)
            if total_ingresos
            else 0
        )

    proveedores_principales = list(
        IngresoMateriaPrima.objects.values("proveedor__nombre")
        .annotate(total_ingresos=Count("id"), peso_total=Sum("peso_neto"))
        .order_by("-total_ingresos", "-peso_total")[:5]
    )

    total_produccion = Paca.objects.count()
    total_vendido = (
        DetalleVenta.objects.aggregate(total=Sum("cantidad_pacas"))["total"] or 0
    )
    total_clientes = Venta.objects.values("cliente_id").distinct().count()
    total_por_cobrar = (
        Venta.objects.filter(estado_pago="pendiente").aggregate(total=Sum("total"))[
            "total"
        ]
        or 0
    )

    # Tendencia de los últimos 30 días.
    tendencia = list(
        Venta.objects.filter(fecha__gte=desde)
        .values("fecha")
        .annotate(total=Sum("total"))
        .order_by("fecha")
    )

    datos_graficos = {
        "produccion": {
            "labels": [
                f"{item['detalle__producto__nombre']} · {item['detalle__color__nombre']}"
                for item in produccion_por_modelo
            ],
            "valores": [item["total"] for item in produccion_por_modelo],
            "colores": [item["color_hex"] for item in produccion_por_modelo],
        },
        "productos": {
            "labels": [
                f"{item['modelo__nombre']} · {item['color__nombre']}"
                for item in productos_mas_vendidos
            ],
            "valores": [item["cantidad_total"] for item in productos_mas_vendidos],
        },
        "clientes": {
            "labels": [cliente["cliente__nombre"] for cliente in clientes_activos],
            "valores": [float(cliente["total_ventas"] or 0) for cliente in clientes_activos],
            "pacas": [cliente["total_pacas"] for cliente in clientes_activos],
        },
        "proveedores": {
            "labels": [
                item["proveedor__nombre"] for item in proveedores_principales
            ],
            "valores": [item["total_ingresos"] for item in proveedores_principales],
        },
        "tendencia": {
            "labels": [item["fecha"].strftime("%d/%m") for item in tendencia],
            "valores": [float(item["total"] or 0) for item in tendencia],
        },
    }

    context = {
        "produccion_por_modelo": produccion_por_modelo,
        "productos_mas_vendidos": productos_mas_vendidos,
        "clientes_activos": clientes_activos,
        "proveedores_principales": proveedores_principales,
        "total_produccion": total_produccion,
        "total_vendido": total_vendido,
        "total_ingresos": total_ingresos,
        "total_clientes": total_clientes,
        "total_por_cobrar": total_por_cobrar,
        "datos_graficos": datos_graficos,
        "fecha_corte": hoy,
    }

    return render(request, "analytics/dashboard_analytics.html", context)
