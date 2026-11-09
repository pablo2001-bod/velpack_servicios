"""Cálculo de stock compartido entre el dashboard y el módulo de inventario.

El stock real siempre se obtiene de la misma forma: todo lo producido menos
todo lo vendido para una combinación de producto(s) y color. Tener esta lógica
en un único lugar evita que ambos paneles muestren valores distintos.
"""

from django.db.models import Sum

from apps.produccion.models import DetalleProduccion
from apps.ventas.models import DetalleVenta

# Colores y modelos que se muestran en la matriz de stock. El orden importa
# porque define las columnas de las tablas del dashboard.
COLORES_STOCK = (
    "Amarillo",
    "Verde",
    "Gris",
    "Natural",
    "Morado",
    "Palo de Rosa",
)

CLAVES_COLOR = {
    "Amarillo": "amarillo",
    "Verde": "verde",
    "Gris": "gris",
    "Natural": "natural",
    "Morado": "morado",
    "Palo de Rosa": "palorosa",
}

# (sufijo en el contexto, clave del total, nombres de producto)
MODELOS_STOCK = (
    ("inicial", "total_inicial", ("Cubeta Inicial",)),
    ("mediana", "total_mediana", ("Cubeta Mediana",)),
    ("gruesa", "total_gruesa", ("Cubeta Gruesa",)),
    ("extra", "total_extragruesa", ("Cubeta Extragruesa", "Cubeta Extra")),
)

PRODUCTOS_SEGUNDA = ("Cubetas Especial", "Cubeta Segunda", "Cubeta de Segunda")

# Color representativo de cada línea para gráficos y puntos de la tabla.
COLORES_INFO = {
    "Amarillo": "#f2c200",
    "Verde": "#2e7d32",
    "Gris": "#6b7280",
    "Natural": "#c8a97e",
    "Morado": "#7c3aed",
    "Palo de Rosa": "#e07a9a",
}

# (clave, nombre visible, clave del total, icono Bootstrap, color)
RESUMEN_MODELOS = (
    ("inicial", "Inicial", "total_inicial", "bi-box-seam", "#2e7d32"),
    ("mediana", "Mediana", "total_mediana", "bi-box", "#1565c0"),
    ("gruesa", "Gruesa", "total_gruesa", "bi-boxes", "#f59e0b"),
    ("extragruesa", "Extragruesa", "total_extragruesa", "bi-stack", "#7c3aed"),
    ("especial", "Cubetas Especial", "total_cubetas_especial", "bi-stars", "#0d9488"),
)


def _como_lista(nombres_producto):
    if isinstance(nombres_producto, str):
        return [nombres_producto]
    return list(nombres_producto)


def obtener_stock_real(nombres_producto, nombre_color):
    """Stock neto (producido - vendido) de uno o varios productos y un color."""
    nombres_producto = _como_lista(nombres_producto)

    producido = (
        DetalleProduccion.objects.filter(
            producto__nombre__in=nombres_producto,
            color__nombre__iexact=nombre_color,
        ).aggregate(total=Sum("cantidad_pacas"))["total"]
        or 0
    )

    vendido = (
        DetalleVenta.objects.filter(
            modelo__nombre__in=nombres_producto,
            color__nombre__iexact=nombre_color,
        ).aggregate(total=Sum("cantidad_pacas"))["total"]
        or 0
    )

    return max(0, producido - vendido)


def obtener_total_modelo(nombres_producto):
    """Stock neto total de uno o varios productos sumando todos sus colores."""
    nombres_producto = _como_lista(nombres_producto)

    producido = (
        DetalleProduccion.objects.filter(
            producto__nombre__in=nombres_producto
        ).aggregate(total=Sum("cantidad_pacas"))["total"]
        or 0
    )

    vendido = (
        DetalleVenta.objects.filter(
            modelo__nombre__in=nombres_producto
        ).aggregate(total=Sum("cantidad_pacas"))["total"]
        or 0
    )

    return max(0, producido - vendido)


def calcular_stock_inventario():
    """Devuelve el contexto completo de la matriz de stock.

    Las claves resultantes coinciden con las que usan las plantillas
    (``amarillo_inicial``, ``total_extragruesa``, etc.).
    """
    contexto = {}
    totales = {clave_total: 0 for _, clave_total, _ in MODELOS_STOCK}

    for color in COLORES_STOCK:
        clave_color = CLAVES_COLOR[color]
        for sufijo, clave_total, productos in MODELOS_STOCK:
            cantidad = obtener_stock_real(productos, color)
            contexto[f"{clave_color}_{sufijo}"] = cantidad
            totales[clave_total] += cantidad

    contexto.update(totales)
    contexto["total_cubetas_especial"] = obtener_total_modelo(PRODUCTOS_SEGUNDA)
    contexto["total_matriz"] = sum(totales.values())
    contexto["total_general"] = (
        contexto["total_matriz"] + contexto["total_cubetas_especial"]
    )

    filas_stock = []
    for color in COLORES_STOCK:
        clave_color = CLAVES_COLOR[color]
        valores = [
            contexto[f"{clave_color}_{sufijo}"] for sufijo, _, _ in MODELOS_STOCK
        ]
        filas_stock.append(
            {
                "nombre": color,
                "clave": clave_color,
                "color_hex": COLORES_INFO[color],
                "valores": valores,
                "total": sum(valores),
            }
        )
    contexto["filas_stock"] = filas_stock

    contexto["resumen_modelos"] = [
        {
            "clave": clave,
            "nombre": nombre,
            "total": contexto[clave_total],
            "icono": icono,
            "color": color,
        }
        for clave, nombre, clave_total, icono, color in RESUMEN_MODELOS
    ]

    return contexto
