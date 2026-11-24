from django.test import TestCase

from .forms import IngresoMateriaPrimaForm
from .models import Proveedor


class IngresoMateriaPrimaFormTests(TestCase):
    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Prueba", ruc="0102030405001"
        )

    def test_rechaza_pesos_negativos(self):
        formulario = IngresoMateriaPrimaForm(
            data={
                "proveedor": self.proveedor.id,
                "tipo_material": "CARTON",
                "peso_cargado": "-10",
                "peso_vacio": "2",
                "cantidad": "0",
            }
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("no pueden ser negativos", str(formulario.errors))

    def test_rechaza_peso_vacio_mayor_que_cargado(self):
        formulario = IngresoMateriaPrimaForm(
            data={
                "proveedor": self.proveedor.id,
                "tipo_material": "CARTON",
                "peso_cargado": "10",
                "peso_vacio": "12",
                "cantidad": "0",
            }
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("peso vacío", str(formulario.errors))
