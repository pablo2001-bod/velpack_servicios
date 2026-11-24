from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.clientes.models import Cliente
from apps.transportes.models import Transporte

from .models import Despacho


class GuiaDespachoEditableTests(TestCase):
    def setUp(self):
        self.cliente_web = Cliente.objects.create(
            nombre="Cliente Prueba", ruc="0999999999001", direccion="Latacunga"
        )
        self.transporte = Transporte.objects.create(
            placa="PBA-123",
            identificacion="1712345678001",
            conductor="Conductor Prueba",
            capacidad_kg=1000,
        )
        self.producto = Producto.objects.create(nombre="Inicial", codigo="I")
        self.color = Color.objects.create(nombre="Amarillo", codigo="A")
        usuario = User.objects.create_user(
            username="admin-guia", password="ClaveFuerte123!", is_staff=True
        )
        self.client.force_login(usuario)

    def test_crear_despacho_guarda_datos_editables_de_la_guia(self):
        response = self.client.post(
            reverse("despachos:crear"),
            {
                "cliente": self.cliente_web.id,
                "transporte": self.transporte.id,
                "numero_guia": "GUIA-EDITADA",
                "fecha": timezone.localdate().isoformat(),
                "direccion_entrega": "Salcedo",
                "estado": "PENDIENTE",
                "ruc_emisor": "0999999999002",
                "direccion_emisor": "Nueva dirección",
                "ciudad_emisor": "Quito",
                "contribuyente": "Régimen général",
                "agente_retencion": "Resolución 2",
                "ambiente": "PRUEBAS",
                "emision": "CONTINGENCIA",
                "punto_partida": "QUITO",
                "estado_transporte": "Preparado",
                "motivo": "TRANSFERENCIA",
                "ruta": "QUITO - SALCEDO",
                "correo_empresa": "correo@velpack.com",
                "telefono_empresa": "022222222",
                "detalles-TOTAL_FORMS": "1",
                "detalles-INITIAL_FORMS": "0",
                "detalles-MIN_NUM_FORMS": "0",
                "detalles-MAX_NUM_FORMS": "1000",
                "detalles-0-cantidad": "2",
                "detalles-0-precio": "12.50",
                "detalles-0-variedad": self.producto.id,
                "detalles-0-color": self.color.id,
            },
        )
        self.assertRedirects(response, reverse("despachos:lista"))

        despacho = Despacho.objects.get(numero_guia="GUIA-EDITADA")
        self.assertEqual(despacho.ruc_emisor, "0999999999002")
        self.assertEqual(despacho.motivo, "TRANSFERENCIA")

        detalle = self.client.get(reverse("despachos:ver", args=[despacho.id]))
        self.assertContains(detalle, "0999999999002")
        self.assertContains(detalle, "QUITO - SALCEDO")
