from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.produccion.models import (
    ArchivoEtiquetas,
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
        cls.color = Color.objects.create(
            nombre="Amarillo", codigo="A", hex_color="#ff5722"
        )
        Turno.objects.create(
            nombre="Todo el día",
            hora_inicio=time(0, 0),
            hora_fin=time(23, 59, 59, 999999),
        )

    def tearDown(self):
        for archivo in ArchivoEtiquetas.objects.all():
            archivo.archivo.delete()

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

        response = self.client.post(reverse("operadores:logout_operador"))

        self.assertRedirects(response, reverse("operadores:terminal_operador"))
        self.assertIn("operador_id", self.client.session)

    def test_ids_invalidos_no_generan_error(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        response = self.client.post(
            reverse("operadores:terminal_operador"),
            {"accion": "configurar_color", "color_id": "abc"},
        )
        self.assertRedirects(response, reverse("operadores:terminal_operador"))

        response = self.client.post(
            reverse("operadores:terminal_operador"),
            {"producto_id": "abc", "cantidad_pacas": "1"},
        )
        self.assertRedirects(response, reverse("operadores:terminal_operador"))

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
        self.assertContains(response, "Selecciona un color")
        self.assertContains(response, "color-grid")
        self.assertContains(response, "#ff5722")

    def test_terminal_renderiza_modelos_con_color_elegido(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        response = self.client.get(reverse("operadores:terminal_operador"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Toque el modelo a registrar")
        self.assertContains(response, "Confirmar")

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

    def test_login_fuera_de_ventana_del_turno(self):
        from apps.produccion.models import Turno

        Turno.objects.all().delete()
        response = self.client.post(
            reverse("operadores:login_operador"),
            {"cedula": self.operador.cedula},
        )

        self.assertRedirects(response, reverse("operadores:login_operador"))
        self.assertNotIn("operador_id", self.client.session)

    def test_sesion_se_cierra_automaticamente_despues_del_turno(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session["turno_limite"] = (
            timezone.now() - timedelta(minutes=1)
        ).isoformat()
        session.save()

        response = self.client.get(reverse("operadores:terminal_operador"))

        self.assertRedirects(response, reverse("operadores:login_operador"))
        self.assertNotIn("operador_id", self.client.session)

    def test_registro_no_muestra_descarga_pdf_al_operador(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session["color_id"] = self.color.id
        session.save()

        response = self.client.post(
            reverse("operadores:terminal_operador"),
            {"producto_id": self.producto.id, "cantidad_pacas": "2"},
            follow=True,
        )

        self.assertNotContains(response, "Descargar PDF")
        self.assertIsNone(self.client.session.get("ultimo_pdf_id"))
        self.assertTrue(ArchivoEtiquetas.objects.exists())

    def test_operador_no_puede_descargar_pdf(self):
        session = self.client.session
        session["operador_id"] = self.operador.id
        session.save()

        response = self.client.get(
            reverse("produccion:descargar_pdf", args=[1]),
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
