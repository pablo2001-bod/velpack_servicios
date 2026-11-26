"""Cálculo de stock compartido entre el dashboard y el módulo de inventario."""

from django.db.models import Sum
from django.utils.text import slugify

from apps.catalogos.models import Color, Producto
from apps.produccion.models import DetalleProduccion
from apps.ventas.models import DetalleVenta

LEGACY_COLORES = {
    "amarillo": "amarillo",
    "verde": "verde",
    "gris": "gris",
    "natural": "natural",
    "morado": "morado",
    "palo de rosa": "palorosa",
}

ORDEN_COLORES = {
    "amarillo": 0,
    "verde": 1,
    "gris": 2,
    "natural": 3,
    "morado": 4,
    "palorosa": 5,
}

ORDEN_MODELOS = {
    "inicial": 0,
    "mediana": 1,
    "gruesa": 2,
    "extra": 3,
    "extragruesa": 3,
}

ICONOS_MODELOS = (
    "bi-box-seam",
    "bi-box",
    "bi-boxes",
    "bi-stack",
    "bi-stars",
    "bi-cube",
)

COLORES_MODELOS = (
    "#2e7d32",
    "#1565c0",
    "#f59e0b",
    "#7c3aed",
    "#0d9488",
    "#e07a9a",
)


def _como_lista(nombres_producto):
    if isinstance(nombres_producto, str):
        return [nombres_producto]
    return list(nombres_producto)


def _clave_color(color):
    return LEGACY_COLORES.get(
        color.nombre.strip().casefold(),
        slugify(color.nombre).replace("-", "") or f"color_{color.id}",
    )


def _clave_modelo(producto):
    nombre = producto.nombre.strip().casefold()
    if nombre.startswith("cubeta "):
        nombre = nombre[7:]
    nombre = nombre.replace("extragruesa", "extra")
    return slugify(nombre).replace("-", "_") or f"modelo_{producto.id}"


def _clave_total_modelo(clave):
    if clave == "extra":
        return "total_extragruesa"
    return f"total_{clave}"


def _stock_neto(productos, color):
    ids = [producto.id for producto in productos]
    if not ids:
        return 0

    producido = (
        DetalleProduccion.objects.filter(
            producto_id__in=ids,
            color=color,
        ).aggregate(total=Sum("cantidad_pacas"))["total"]
        or 0
    )
    vendido = (
        DetalleVenta.objects.filter(
            modelo_id__in=ids,
            color=color,
        ).aggregate(total=Sum("cantidad_pacas"))["total"]
        or 0
    )
    return max(0, producido - vendido)


def _stock_total(productos):
    ids = [producto.id for producto in productos]
    if not ids:
        return 0

    producido = (
        DetalleProduccion.objects.filter(producto_id__in=ids).aggregate(
            total=Sum("cantidad_pacas")
        )["total"]
        or 0
    )
    vendido = (
        DetalleVenta.objects.filter(modelo_id__in=ids).aggregate(
            total=Sum("cantidad_pacas")
        )["total"]
        or 0
    )
    return max(0, producido - vendido)


def obtener_stock_real(nombres_producto, nombre_color):
    productos = list(Producto.objects.filter(nombre__in=_como_lista(nombres_producto)))
    color = Color.objects.filter(nombre__iexact=nombre_color).first()
    if not color:
        return 0
    return _stock_neto(productos, color)


def obtener_total_modelo(nombres_producto):
    productos = list(Producto.objects.filter(nombre__in=_como_lista(nombres_producto)))
    return _stock_total(productos)


def calcular_stock_inventario():
    colores = list(Color.objects.filter(activo=True))
    productos = list(Producto.objects.filter(activo=True))

    colores.sort(
        key=lambda color: (
            ORDEN_COLORES.get(_clave_color(color), 99),
            color.nombre.casefold(),
        )
    )
    productos.sort(
        key=lambda producto: (
            ORDEN_MODELOS.get(_clave_modelo(producto), 99),
            producto.nombre.casefold(),
        )
    )

    contexto = {}
    claves_color_usadas = set()
    claves_modelo_usadas = set()
    totales_modelo = {}
    columnas = []

    for indice, producto in enumerate(productos):
        clave = _clave_modelo(producto)
        if clave in claves_modelo_usadas:
            clave = f"{clave}_{producto.id}"
        claves_modelo_usadas.add(clave)

        clave_total = _clave_total_modelo(clave)
        if clave_total in contexto:
            clave_total = f"{clave_total}_{producto.id}"

        columnas.append(
            {
                "id": producto.id,
                "nombre": producto.nombre,
                "clave": clave,
                "total_key": clave_total,
            }
        )
        totales_modelo[producto.id] = 0

    filas_stock = []
    for color in colores:
        clave_color = _clave_color(color)
        if clave_color in claves_color_usadas:
            clave_color = f"{clave_color}_{color.id}"
        claves_color_usadas.add(clave_color)

        valores = []
        total_fila = 0
        for columna in columnas:
            producto = next(p for p in productos if p.id == columna["id"])
            cantidad = _stock_neto([producto], color)
            valores.append(cantidad)
            total_fila += cantidad
            totales_modelo[producto.id] += cantidad
            contexto[f"{clave_color}_{columna['clave']}"] = cantidad

        filas_stock.append(
            {
                "id": color.id,
                "nombre": color.nombre,
                "clave": clave_color,
                "color_hex": color.hex_color,
                "valores": valores,
                "total": total_fila,
            }
        )

    for columna in columnas:
        cantidad_total = totales_modelo[columna["id"]]
        contexto[columna["total_key"]] = cantidad_total
        columna["total"] = cantidad_total

    for clave_total in (
        "total_inicial",
        "total_mediana",
        "total_gruesa",
        "total_extragruesa",
    ):
        contexto.setdefault(clave_total, 0)

    contexto["columnas_modelos"] = columnas
    contexto["filas_stock"] = filas_stock
    contexto["total_cubetas_especial"] = sum(
        totales_modelo[producto.id] for producto in productos if producto.es_segunda
    )
    contexto["total_matriz"] = sum(totales_modelo.values())
    contexto["total_general"] = contexto["total_matriz"]
    contexto["resumen_modelos"] = [
        {
            "clave": columna["clave"],
            "nombre": columna["nombre"],
            "total": totales_modelo[columna["id"]],
            "icono": ICONOS_MODELOS[indice % len(ICONOS_MODELOS)],
            "color": COLORES_MODELOS[indice % len(COLORES_MODELOS)],
        }
        for indice, columna in enumerate(columnas)
    ]

    return contexto
