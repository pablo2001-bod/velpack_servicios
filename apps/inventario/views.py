from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from apps.produccion.models import DetalleProduccion
from apps.proveedores.models import IngresoMateriaPrima
from apps.ventas.models import DetalleVenta  # Importamos el modelo de ventas

def obtener_stock_real(nombres_producto, nombre_color):
    """
    Suma todo lo producido y le resta todo lo vendido para un producto y color dados.
    Acepta un nombre de producto o una lista de nombres de productos.
    """
    if isinstance(nombres_producto, str):
        nombres_producto = [nombres_producto]

    # Total producido
    producido = DetalleProduccion.objects.filter(
        producto__nombre__in=nombres_producto,
        color__nombre__iexact=nombre_color
    ).aggregate(total=Sum('cantidad_pacas'))['total'] or 0

    # Total vendido
    vendido = DetalleVenta.objects.filter(
        modelo__nombre__in=nombres_producto,
        color__nombre__iexact=nombre_color
    ).aggregate(total=Sum('cantidad_pacas'))['total'] or 0

    return max(0, producido - vendido)

def obtener_total_modelo(nombres_producto):
    """Calcula el stock total neto por modelo de producto (sumando todos sus colores)."""
    if isinstance(nombres_producto, str):
        nombres_producto = [nombres_producto]

    producido = DetalleProduccion.objects.filter(
        producto__nombre__in=nombres_producto
    ).aggregate(total=Sum('cantidad_pacas'))['total'] or 0

    vendido = DetalleVenta.objects.filter(
        modelo__nombre__in=nombres_producto
    ).aggregate(total=Sum('cantidad_pacas'))['total'] or 0

    return max(0, producido - vendido)


@login_required
def dashboard_inventario(request):
    # 1. Desglose de Materia Prima por Tipo
    materia_prima_por_tipo = (
        IngresoMateriaPrima.objects
        .values('tipo_material')
        .annotate(total_peso=Sum('peso_neto'))
        .order_by('-total_peso')
    )

    # 2. Matriz de Stock Real por Color y Modelo (Producido - Vendido)
    # AMARILLO
    amarillo_inicial = obtener_stock_real("Cubeta Inicial", "Amarillo")
    amarillo_mediana = obtener_stock_real("Cubeta Mediana", "Amarillo")
    amarillo_gruesa = obtener_stock_real("Cubeta Gruesa", "Amarillo")
    amarillo_extra = obtener_stock_real(["Cubeta Extragruesa", "Cubeta Extra"], "Amarillo")

    # VERDE
    verde_inicial = obtener_stock_real("Cubeta Inicial", "Verde")
    verde_mediana = obtener_stock_real("Cubeta Mediana", "Verde")
    verde_gruesa = obtener_stock_real("Cubeta Gruesa", "Verde")
    verde_extra = obtener_stock_real(["Cubeta Extragruesa", "Cubeta Extra"], "Verde")

    # GRIS
    gris_inicial = obtener_stock_real("Cubeta Inicial", "Gris")
    gris_mediana = obtener_stock_real("Cubeta Mediana", "Gris")
    gris_gruesa = obtener_stock_real("Cubeta Gruesa", "Gris")
    gris_extra = obtener_stock_real(["Cubeta Extragruesa", "Cubeta Extra"], "Gris")

    # NATURAL
    natural_inicial = obtener_stock_real("Cubeta Inicial", "Natural")
    natural_mediana = obtener_stock_real("Cubeta Mediana", "Natural")
    natural_gruesa = obtener_stock_real("Cubeta Gruesa", "Natural")
    natural_extra = obtener_stock_real(["Cubeta Extragruesa", "Cubeta Extra"], "Natural")

    # MORADO
    morado_inicial = obtener_stock_real("Cubeta Inicial", "Morado")
    morado_mediana = obtener_stock_real("Cubeta Mediana", "Morado")
    morado_gruesa = obtener_stock_real("Cubeta Gruesa", "Morado")
    morado_extra = obtener_stock_real(["Cubeta Extragruesa", "Cubeta Extra"], "Morado")

    # PALO DE ROSA
    palorosa_inicial = obtener_stock_real("Cubeta Inicial", "Palo de Rosa")
    palorosa_mediana = obtener_stock_real("Cubeta Mediana", "Palo de Rosa")
    palorosa_gruesa = obtener_stock_real("Cubeta Gruesa", "Palo de Rosa")
    palorosa_extra = obtener_stock_real(["Cubeta Extragruesa", "Cubeta Extra"], "Palo de Rosa")

    # 3. Totales por Columna (Sumatoria real de las filas)
    total_inicial = amarillo_inicial + verde_inicial + gris_inicial + natural_inicial + morado_inicial + palorosa_inicial
    total_mediana = amarillo_mediana + verde_mediana + gris_mediana + natural_mediana + morado_mediana + palorosa_mediana
    total_gruesa = amarillo_gruesa + verde_gruesa + gris_gruesa + natural_gruesa + morado_gruesa + palorosa_gruesa
    total_extragruesa = amarillo_extra + verde_extra + gris_extra + natural_extra + morado_extra + palorosa_extra

    # Total para Cubetas Especial / Segunda
    total_cubetas_especial = obtener_total_modelo(["Cubetas Especial", "Cubeta Segunda"])

    context = {
        'materia_prima_por_tipo': materia_prima_por_tipo,
        'total_cubetas_especial': total_cubetas_especial,

        # Totales para el pie de tabla
        'total_inicial': total_inicial,
        'total_mediana': total_mediana,
        'total_gruesa': total_gruesa,
        'total_extragruesa': total_extragruesa,

        # Amarillo
        'amarillo_inicial': amarillo_inicial,
        'amarillo_mediana': amarillo_mediana,
        'amarillo_gruesa': amarillo_gruesa,
        'amarillo_extra': amarillo_extra,

        # Verde
        'verde_inicial': verde_inicial,
        'verde_mediana': verde_mediana,
        'verde_gruesa': verde_gruesa,
        'verde_extra': verde_extra,

        # Gris
        'gris_inicial': gris_inicial,
        'gris_mediana': gris_mediana,
        'gris_gruesa': gris_gruesa,
        'gris_extra': gris_extra,

        # Natural
        'natural_inicial': natural_inicial,
        'natural_mediana': natural_mediana,
        'natural_gruesa': natural_gruesa,
        'natural_extra': natural_extra,

        # Morado
        'morado_inicial': morado_inicial,
        'morado_mediana': morado_mediana,
        'morado_gruesa': morado_gruesa,
        'morado_extra': morado_extra,

        # Palo de Rosa
        'palorosa_inicial': palorosa_inicial,
        'palorosa_mediana': palorosa_mediana,
        'palorosa_gruesa': palorosa_gruesa,
        'palorosa_extra': palorosa_extra,
    }

    return render(request, 'inventario/dashboard.html', context)