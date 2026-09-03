from django.shortcuts import render
from django.db.models import Count, Sum
from apps.produccion.models import Paca
from apps.ventas.models import DetalleVenta, Venta
from apps.clientes.models import Cliente
from apps.proveedores.models import IngresoMateriaPrima

def dashboard_analiticas(request):
    # 1. Producción corregida usando 'detalle__producto__nombre' y 'detalle__color__nombre'
    produccion_por_modelo = Paca.objects.values(
        'detalle__producto__nombre', 'detalle__color__nombre'
    ).annotate(total=Count('id')).order_by('-total')
    
    # 2. Ventas
    productos_mas_vendidos = DetalleVenta.objects.values(
        'modelo__nombre', 'color__nombre'
    ).annotate(cantidad_total=Sum('cantidad_pacas')).order_by('-cantidad_total')
    
    # 3. Clientes más activos
    clientes_activos = Venta.objects.values(
        'cliente__nombre'
    ).annotate(total_compras=Count('id')).order_by('-total_compras')[:5]
    
    # 4. Proveedores principales
    proveedores_principales = IngresoMateriaPrima.objects.values(
        'proveedor__nombre'
    ).annotate(total_ingresos=Count('id')).order_by('-total_ingresos')[:5]

    context = {
        'produccion_por_modelo': produccion_por_modelo,
        'productos_mas_vendidos': productos_mas_vendidos,
        'clientes_activos': clientes_activos,
        'proveedores_principales': proveedores_principales,
    }
    
    return render(request, 'analytics/dashboard_analytics.html', context)