from datetime import time

from django.test import TestCase
from django.urls import reverse

from apps.catalogos.models import Color, Producto
from apps.produccion.models import (
    DetalleProduccion,
    Operador,
    Paca,
    Produccion,
    Turno,
)


class TerminalOperadorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operador = Operador.objects.create(
            nombre_completo="Ana Ruiz", cedula="1234567890"
        )
        cls.producto = Producto.objects.create(nombre="Cubeta Inicial", codigo="I")
        cls.color = Color.objects.create(nombre="Amarillo", codigo="A")
        Turno.objects.create(
            nombre="Todo el día",
            hora_inicio=time(0, 0),
            hora_fin=time(23, 59, 59, 999999),
        )

    def test_login_redirige_a_terminal(self):
        response = self.client.post(
            reverse("operadores:login_operador"),
            {"cedula": self.operador.cedula},
        )

        self.assertRedirects(response, reverse("operadores:terminal_operador"))

    def test_registrar_pacas_desde_terminal(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        response = self.client.post(
            reverse("operadores:terminal_operador"),
            {"producto_id": self.producto.id, "cantidad_pacas": "2"},
        )

        self.assertTrue(self.client.session.get("imprimir_ahora"))
        self.assertRedirects(response, reverse("operadores:terminal_operador"))
        self.assertEqual(Paca.objects.count(), 2)
        detalle = DetalleProduccion.objects.get()
        self.assertEqual(detalle.cantidad_pacas, 2)

    def test_no_permite_cerrar_sesion_durante_turno(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        response = self.client.get(reverse("operadores:logout_operador"))

        self.assertRedirects(response, reverse("operadores:terminal_operador"))
        self.assertIn("operador_id", self.client.session)

    def test_operador_envia_observacion_al_administrador(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        response = self.client.post(
            reverse("operadores:terminal_operador"),
            {"accion": "registrar_observacion", "observacion": "Falta material"},
        )

        self.assertRedirects(response, reverse("operadores:terminal_operador"))
        produccion = Produccion.objects.get()
        self.assertIn("Falta material", produccion.observacion)
        self.assertIn(self.operador.nombre_completo, produccion.observacion)

    def test_terminal_renderiza_seleccion_de_color(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session.save()

        response = self.client.get(reverse("operadores:terminal_operador"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selecciona tu color de trabajo")
        self.assertContains(response, "Etiquetas de hoy")

    def test_terminal_renderiza_modelos_con_color_elegido(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        response = self.client.get(reverse("operadores:terminal_operador"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Toque el modelo a registrar")
        self.assertContains(response, "Confirmar e imprimir")

    def test_etiquetas_incluyen_barcode_qr_y_lote(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        self.client.post(
            reverse("operadores:terminal_operador"),
            {"producto_id": self.producto.id, "cantidad_pacas": "51"},
        )

        response = self.client.get(reverse("operadores:etiquetas"))
        contenido = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("data:image/svg+xml;base64", contenido)
        self.assertIn("VELPACK S.A.", contenido)
        self.assertIn("L01", contenido)
        self.assertIn("L02", contenido)
        self.assertIn("Código de barras", contenido)
        self.assertIn("QR", contenido)
