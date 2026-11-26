from datetime import time
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogos.models import Color, Producto
from apps.proveedores.models import IngresoMateriaPrima, Proveedor
from apps.produccion.models import (
    ArchivoEtiquetas,
    ConfiguracionProduccion,
    ConsumoMateriaPrima,
    DetalleProduccion,
    Operador,
    Paca,
    ParametroProduccion,
    Produccion,
    Turno,
)
from apps.produccion.pdf import generar_archivo_pdf
from apps.produccion.services import (
    generar_pacas,
    obtener_pacas_por_lote,
    obtener_stock_materia_prima,
    recalcular_lotes_y_codigos,
    registrar_pacas,
)


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

    def test_genera_numeracion_y_lotes_de_28(self):
        generar_pacas(self.detalle, 30)
        pacas = list(Paca.objects.order_by("numero_paca"))

        self.assertEqual(len(pacas), 30)
        self.assertEqual((pacas[0].numero_paca, pacas[0].lote), (1, 1))
        self.assertEqual((pacas[27].numero_paca, pacas[27].lote), (28, 1))
        self.assertEqual((pacas[28].numero_paca, pacas[28].lote), (29, 2))

        prefijo = f"AR{self.produccion.fecha.strftime('%d%m%y')}IA"
        self.assertEqual(pacas[0].codigo_unico, f"{prefijo}001L01")

    def test_lote_configurable_y_recalculo_automatico(self):
        self.assertEqual(obtener_pacas_por_lote(), 28)
        generar_pacas(self.detalle, 30)
        self.assertEqual(Paca.objects.get(numero_paca=29).lote, 2)

        configuracion = ConfiguracionProduccion.obtener()
        configuracion.pacas_por_lote = 50
        configuracion.save()

        self.assertEqual(Paca.objects.get(numero_paca=29).lote, 1)
        self.assertTrue(
            Paca.objects.get(numero_paca=29).codigo_unico.endswith("L01")
        )

        generar_pacas(self.detalle, 21)
        self.assertEqual(Paca.objects.get(numero_paca=51).lote, 2)

    def test_recalcular_lotes_y_codigos(self):
        generar_pacas(self.detalle, 3)
        configuracion = ConfiguracionProduccion.obtener()
        configuracion.pacas_por_lote = 1
        configuracion.save()
        self.assertEqual(recalcular_lotes_y_codigos(), 3)
        self.assertEqual(Paca.objects.get(numero_paca=3).lote, 3)
        self.assertTrue(Paca.objects.get(numero_paca=3).codigo_unico.endswith("L03"))

    def test_genera_archivo_pdf(self):
        generar_pacas(self.detalle, 2)
        pacas = list(
            Paca.objects.select_related(
                "detalle__producto", "detalle__color", "detalle__produccion__operador"
            )
        )
        archivo = generar_archivo_pdf(pacas, "Etiquetas de prueba", self.produccion)

        self.assertEqual(archivo.cantidad_pacas, 2)
        self.assertTrue(archivo.archivo.name.endswith(".pdf"))
        with archivo.archivo.open("rb") as contenido:
            self.assertEqual(contenido.read(4), b"%PDF")
        archivo.archivo.delete()

    def test_continua_numeracion_en_llamadas_separadas(self):
        generar_pacas(self.detalle, 2)
        generar_pacas(self.detalle, 1)

        numeros = list(
            Paca.objects.order_by("numero_paca").values_list("numero_paca", flat=True)
        )
        self.assertEqual(numeros, [1, 2, 3])


class CronogramaAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="ClaveAdmin123!"
        )
        self.client.force_login(self.admin)
        self.operador = Operador.objects.create(
            nombre_completo="Ana Ruiz", cedula="1234567890"
        )
        Turno.objects.create(
            nombre="Todo el día", hora_inicio=time(0, 0), hora_fin=time(23, 59, 59)
        )

    def tearDown(self):
        for archivo in ArchivoEtiquetas.objects.all():
            archivo.archivo.delete()

    def test_crear_modelo_y_color_desde_cronograma(self):
        self.client.post(
            reverse("produccion:modelo_crear"),
            {"nombre": "Cubeta Nueva", "codigo": "x", "activo": "on"},
        )
        self.client.post(
            reverse("produccion:color_crear"),
            {"nombre": "Rosado", "codigo": "r", "activo": "on"},
        )

        self.assertTrue(Producto.objects.filter(nombre="Cubeta Nueva", codigo="X").exists())
        self.assertTrue(Color.objects.filter(nombre="Rosado", codigo="R").exists())

    def test_agregar_produccion_genera_pdf(self):
        producto = Producto.objects.create(nombre="Inicial", codigo="I")
        color = Color.objects.create(nombre="Amarillo", codigo="A")

        response = self.client.post(
            reverse("produccion:agregar_produccion"),
            {
                "operador": self.operador.id,
                "observacion": "",
                "items-TOTAL_FORMS": "2",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "1",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-producto": producto.id,
                "items-0-color": color.id,
                "items-0-cantidad_pacas": "3",
                "items-1-producto": producto.id,
                "items-1-color": color.id,
                "items-1-cantidad_pacas": "2",
            },
        )

        self.assertRedirects(response, reverse("produccion:registrar"))
        self.assertEqual(Paca.objects.count(), 5)
        self.assertTrue(ArchivoEtiquetas.objects.exists())

    def test_usuario_normal_no_puede_modificar_catalogos(self):
        usuario = User.objects.create_user(
            username="normal", password="ClaveNormal123!"
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("produccion:modelo_crear"))

        self.assertEqual(response.status_code, 302)

    def test_get_no_elimina_modelos_ni_colores(self):
        producto = Producto.objects.create(nombre="Modelo Prueba", codigo="M")
        color = Color.objects.create(nombre="Color Prueba", codigo="C")

        self.assertEqual(
            self.client.get(
                reverse("produccion:modelo_eliminar", args=[producto.id])
            ).status_code,
            405,
        )
        self.assertEqual(
            self.client.get(
                reverse("produccion:color_eliminar", args=[color.id])
            ).status_code,
            405,
        )
        self.assertTrue(Producto.objects.filter(pk=producto.id).exists())
        self.assertTrue(Color.objects.filter(pk=color.id).exists())


class ParametrosProduccionTests(TestCase):
    def setUp(self):
        self.color = Color.objects.create(nombre="Azul", codigo="Z")
        self.producto = Producto.objects.create(nombre="Inicial", codigo="I")
        self.operador = Operador.objects.create(
            nombre_completo="Ana Ruiz", cedula="1234567890"
        )
        self.turno = Turno.objects.create(
            nombre="Todo el día",
            hora_inicio=time(0, 0),
            hora_fin=time(23, 59, 59),
        )
        self.produccion = Produccion.objects.create(
            fecha=timezone.localdate(),
            operador=self.operador,
            turno=self.turno,
        )
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Prueba", ruc="0102030405001"
        )

    def _crear_ingreso(self, tipo, cargado, vacio):
        IngresoMateriaPrima.objects.create(
            proveedor=self.proveedor,
            tipo_material=tipo,
            peso_cargado=Decimal(str(cargado)),
            peso_vacio=Decimal(str(vacio)),
        )

    def test_descuenta_insumos_configurados_por_color(self):
        self._crear_ingreso("CARTON", 100, 10)
        self._crear_ingreso("DUPLEX", 50, 5)
        ParametroProduccion.objects.create(
            color=self.color,
            tipo_material="CARTON",
            cantidad_por_paca=Decimal("2"),
        )
        ParametroProduccion.objects.create(
            color=self.color,
            tipo_material="DUPLEX",
            cantidad_por_paca=Decimal("0.5"),
        )

        registrar_pacas(self.produccion, self.producto, self.color, 3)

        consumos = {
            consumo.tipo_material: consumo.cantidad_kg
            for consumo in ConsumoMateriaPrima.objects.all()
        }
        self.assertEqual(consumos["CARTON"], Decimal("6.000"))
        self.assertEqual(consumos["DUPLEX"], Decimal("1.500"))

        stock = {
            item["tipo_material"]: item["disponible"]
            for item in obtener_stock_materia_prima()
        }
        self.assertEqual(stock["CARTON"], Decimal("84.00"))
        self.assertEqual(stock["DUPLEX"], Decimal("43.50"))

    def test_falta_de_stock_no_registra_pacas(self):
        ParametroProduccion.objects.create(
            color=self.color,
            tipo_material="CARTON",
            cantidad_por_paca=Decimal("100"),
        )

        with self.assertRaises(ValueError):
            registrar_pacas(self.produccion, self.producto, self.color, 2)

        self.assertEqual(Paca.objects.count(), 0)
        self.assertEqual(DetalleProduccion.objects.count(), 0)
        self.assertEqual(ConsumoMateriaPrima.objects.count(), 0)

    def test_sin_parametros_no_descuenta_materia_prima(self):
        registrar_pacas(self.produccion, self.producto, self.color, 2)

        self.assertEqual(Paca.objects.count(), 2)
        self.assertEqual(ConsumoMateriaPrima.objects.count(), 0)

    def test_admin_gestiona_parametros(self):
        admin = User.objects.create_superuser(
            username="admin", password="ClaveAdmin123!"
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("produccion:parametros"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("produccion:parametro_crear"),
            {
                "color": self.color.id,
                "tipo_material": "TINTE_AMARILLO",
                "cantidad_por_paca": "1.25",
                "activo": "on",
            },
        )
        self.assertRedirects(response, reverse("produccion:parametros"))
        parametro = ParametroProduccion.objects.get(tipo_material="TINTE_AMARILLO")

        response = self.client.post(
            reverse("produccion:parametro_eliminar", args=[parametro.id])
        )
        self.assertRedirects(response, reverse("produccion:parametros"))
        self.assertFalse(ParametroProduccion.objects.filter(pk=parametro.id).exists())
