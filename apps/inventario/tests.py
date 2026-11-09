from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.clientes.models import Cliente
from apps.inventario.services import calcular_stock_inventario, obtener_stock_real
from apps.produccion.models import DetalleProduccion, Operador, Produccion, Turno
from apps.ventas.models import DetalleVenta, Venta


class StockInventarioTests(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(nombre="Cubeta Inicial", codigo="I")
        self.color = Color.objects.create(nombre="Amarillo", codigo="A")
        self.operador = Operador.objects.create(
            nombre_completo="Ana Ruiz", cedula="1234567890"
        )
        self.turno = Turno.objects.create(
            nombre="Mañana", hora_inicio=time(6, 0), hora_fin=time(14, 0)
        )
        self.produccion = Produccion.objects.create(
            fecha=timezone.localdate(),
            turno=self.turno,
            operador=self.operador,
        )
        self.detalle_produccion = DetalleProduccion.objects.create(
            produccion=self.produccion,
            producto=self.producto,
            color=self.color,
            cantidad_pacas=10,
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            ruc="0102030405001",
            direccion="Quito",
        )

    def test_stock_es_producido_menos_vendido(self):
        self.assertEqual(obtener_stock_real("Cubeta Inicial", "Amarillo"), 10)

        venta = Venta.objects.create(numero_factura="F-001", cliente=self.cliente)
        DetalleVenta.objects.create(
            venta=venta,
            modelo=self.producto,
            color=self.color,
            cantidad_pacas=3,
            precio_unitario=Decimal("2.50"),
            subtotal=Decimal("7.50"),
        )

        self.assertEqual(obtener_stock_real("Cubeta Inicial", "Amarillo"), 7)
        # El color se compara sin distinguir mayúsculas.
        self.assertEqual(obtener_stock_real("Cubeta Inicial", "amarillo"), 7)

    def test_contexto_de_stock_usa_las_claves_de_las_plantillas(self):
        contexto = calcular_stock_inventario()

        self.assertEqual(contexto["amarillo_inicial"], 10)
        self.assertEqual(contexto["total_inicial"], 10)
        self.assertEqual(contexto["total_extragruesa"], 0)
        self.assertEqual(contexto["total_cubetas_especial"], 0)
