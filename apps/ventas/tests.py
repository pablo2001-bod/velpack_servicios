from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.clientes.models import Cliente

from .models import Venta


class PagosVentaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_superuser(
            username="admin", password="ClaveAdmin123!"
        )
        self.client.force_login(self.usuario)
        self.cliente = Cliente.objects.create(
            nombre="Cliente Prueba",
            ruc="0102030405001",
            telefono="0999999999",
            correo="cliente@example.com",
            direccion="Direccion",
        )
        self.venta = Venta.objects.create(
            numero_factura="FAC-001",
            cliente=self.cliente,
            metodo_pago="efectivo",
            estado_pago="pendiente",
        )

    def test_get_no_actualiza_pago(self):
        response = self.client.get(
            reverse("ventas:actualizar_estado_pago", args=[self.venta.id])
        )

        self.assertEqual(response.status_code, 405)

    def test_rechaza_metodo_pago_invalido(self):
        response = self.client.post(
            reverse("ventas:actualizar_estado_pago", args=[self.venta.id]),
            {"metodo_pago": "cheque", "estado_pago": "pagado"},
        )

        self.assertRedirects(response, reverse("ventas:lista_ventas"))
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.metodo_pago, "efectivo")
        self.assertEqual(self.venta.estado_pago, "pendiente")
