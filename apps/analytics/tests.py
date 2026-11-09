from datetime import time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.clientes.models import Cliente
from apps.produccion.models import DetalleProduccion, Operador, Produccion, Turno
from apps.ventas.models import DetalleVenta, Venta


class PanelAnaliticasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user(
            username="analista", password="clave-segura"
        )
        cls.producto = Producto.objects.create(nombre="Cubeta Inicial", codigo="I")
        cls.color = Color.objects.create(nombre="Amarillo", codigo="A")
        cls.operador = Operador.objects.create(
            nombre_completo="Ana Ruiz", cedula="1234567890"
        )
        cls.turno = Turno.objects.create(
            nombre="Mañana", hora_inicio=time(6, 0), hora_fin=time(14, 0)
        )
        cls.produccion = Produccion.objects.create(
            fecha=timezone.localdate(),
            turno=cls.turno,
            operador=cls.operador,
        )
        DetalleProduccion.objects.create(
            produccion=cls.produccion,
            producto=cls.producto,
            color=cls.color,
            cantidad_pacas=100,
        )

        cls.cliente_bajo = Cliente.objects.create(
            nombre="Cliente Bajo", ruc="0102030405", direccion="Quito"
        )
        cls.cliente_alto = Cliente.objects.create(
            nombre="Cliente Alto", ruc="0102030406", direccion="Ambato"
        )

        venta_baja = Venta.objects.create(
            numero_factura="F-001", cliente=cls.cliente_bajo
        )

        DetalleVenta.objects.create(
            venta=venta_baja,
            modelo=cls.producto,
            color=cls.color,
            cantidad_pacas=1,
            precio_unitario=10,
            subtotal=10,
        )

        venta_alta = Venta.objects.create(
            numero_factura="F-002", cliente=cls.cliente_alto
        )
        DetalleVenta.objects.create(
            venta=venta_alta,
            modelo=cls.producto,
            color=cls.color,
            cantidad_pacas=10,
            precio_unitario=10,
            subtotal=100,
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_clientes_activos_se_calculan_desde_las_ventas(self):
        response = self.client.get(reverse("analytics:panel"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["clientes_activos"][0]["cliente__nombre"],
            "Cliente Alto",
        )
        self.assertNotContains(response, "Danilo Tisalema")
        self.assertContains(response, "Cliente Alto")

    def test_totales_reflejan_ventas_y_produccion(self):
        response = self.client.get(reverse("analytics:panel"))

        self.assertEqual(response.context["total_vendido"], 11)
        self.assertEqual(float(response.context["total_ingresos"]), 110.0)
        self.assertEqual(response.context["total_clientes"], 2)
