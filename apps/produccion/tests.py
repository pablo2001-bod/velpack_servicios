from datetime import time

from django.test import TestCase
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.produccion.models import (
    DetalleProduccion,
    Operador,
    Paca,
    Produccion,
    Turno,
)
from apps.produccion.services import generar_pacas


class OperadorCredencialTests(TestCase):
    def test_codigo_de_acceso_y_busqueda_por_credencial(self):
        operador = Operador.objects.create(
            nombre_completo="Pedro Torres", cedula="0102030405"
        )

        self.assertEqual(operador.obtener_iniciales(), "PT")
        self.assertEqual(operador.obtener_codigo_acceso(), "PT0405")
        self.assertEqual(Operador.buscar_por_credencial("PT0405"), operador)
        self.assertEqual(Operador.buscar_por_credencial("0102030405"), operador)
        self.assertIsNone(Operador.buscar_por_credencial("NOEXISTE"))

    def test_operador_inactivo_no_puede_ingresar(self):
        operador = Operador.objects.create(
            nombre_completo="Ana Ruiz", cedula="1234567890", activo=False
        )

        self.assertIsNone(Operador.buscar_por_credencial(operador.obtener_codigo_acceso()))


class GenerarPacasTests(TestCase):
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
        self.detalle = DetalleProduccion.objects.create(
            produccion=self.produccion,
            producto=self.producto,
            color=self.color,
            cantidad_pacas=0,
        )

    def test_genera_numeracion_y_lotes_de_50(self):
        generar_pacas(self.detalle, 52)
        pacas = list(Paca.objects.order_by("numero_paca"))

        self.assertEqual(len(pacas), 52)
        self.assertEqual((pacas[0].numero_paca, pacas[0].lote), (1, 1))
        self.assertEqual((pacas[49].numero_paca, pacas[49].lote), (50, 1))
        self.assertEqual((pacas[50].numero_paca, pacas[50].lote), (51, 2))

        prefijo = f"AR{self.produccion.fecha.strftime('%d%m%y')}IA"
        self.assertEqual(pacas[0].codigo_unico, f"{prefijo}001L01")

    def test_continua_numeracion_en_llamadas_separadas(self):
        generar_pacas(self.detalle, 2)
        generar_pacas(self.detalle, 1)

        numeros = list(
            Paca.objects.order_by("numero_paca").values_list("numero_paca", flat=True)
        )
        self.assertEqual(numeros, [1, 2, 3])
