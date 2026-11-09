from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.produccion.labels import preparar_etiquetas

from apps.accounts.models import PerfilUsuario, Rol
from apps.catalogos.models import Color, Producto
from apps.clientes.models import Cliente
from apps.despachos.models import Despacho, DetalleDespacho
from apps.produccion.models import DetalleProduccion, Operador, Produccion, Turno
from apps.produccion.services import generar_pacas
from apps.proveedores.models import IngresoMateriaPrima, Proveedor
from apps.transportes.models import Transporte
from apps.ventas.models import DetalleVenta, Venta


class SmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_superuser(
            username="smoke", email="smoke@example.com", password="test12345"
        )
        rol = Rol.objects.create(nombre="Administrador")
        PerfilUsuario.objects.create(
            usuario=cls.user,
            codigo_operador="SMK",
            rol=rol,
            cargo="Administrador",
            activo=True,
        )

        cls.producto = Producto.objects.create(nombre="Inicial", codigo="I")
        cls.color = Color.objects.create(nombre="Amarillo", codigo="A")
        cls.turno = Turno.objects.create(
            nombre="Matutino", hora_inicio="06:00", hora_fin="14:00"
        )
        cls.operador = Operador.objects.create(
            nombre_completo="Operador Prueba", cedula="0102030405"
        )
        cls.cliente = Cliente.objects.create(
            nombre="Cliente Prueba",
            ruc="0102030405001",
            telefono="0999999999",
            correo="cliente@example.com",
            direccion="Direccion",
        )
        cls.proveedor = Proveedor.objects.create(
            nombre="Proveedor Prueba",
            ruc="0102030405002",
            telefono="0999999999",
            correo="proveedor@example.com",
            direccion="Direccion",
        )
        cls.transporte = Transporte.objects.create(
            placa="ABC1234",
            identificacion="0102030405",
            propietario="Propietario",
            conductor="Conductor",
            telefono="0999999999",
            capacidad_kg=Decimal("1000"),
        )
        cls.ingreso = IngresoMateriaPrima.objects.create(
            proveedor=cls.proveedor,
            tipo_material="polietileno",
            peso_cargado=Decimal("100"),
            peso_vacio=Decimal("10"),
            peso_neto=Decimal("90"),
            cantidad=Decimal("1"),
            observacion="Prueba",
        )

        cls.produccion = Produccion.objects.create(
            fecha=timezone.localdate(),
            turno=cls.turno,
            operador=cls.operador,
            observacion="Prueba",
        )
        cls.detalle = DetalleProduccion.objects.create(
            produccion=cls.produccion,
            producto=cls.producto,
            color=cls.color,
            cantidad_pacas=10,
        )
        generar_pacas(cls.detalle, 10)

        cls.venta = Venta.objects.create(
            numero_factura="FAC-SMOKE",
            cliente=cls.cliente,
            usuario=PerfilUsuario.objects.get(usuario=cls.user),
            metodo_pago="efectivo",
            estado_pago="pendiente",
        )
        DetalleVenta.objects.create(
            venta=cls.venta,
            modelo=cls.producto,
            color=cls.color,
            cantidad_pacas=2,
            precio_unitario=Decimal("10"),
            subtotal=Decimal("20"),
        )

        cls.despacho = Despacho.objects.create(
            cliente=cls.cliente,
            transporte=cls.transporte,
            numero_guia="GUIA-SMOKE",
            fecha=timezone.localdate(),
            direccion_entrega="Direccion",
        )
        DetalleDespacho.objects.create(
            despacho=cls.despacho,
            cantidad=1,
            precio=Decimal("10"),
            variedad=cls.producto,
            color=cls.color,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _get(self, url, **kwargs):
        response = self.client.get(url, **kwargs)
        self.assertIn(response.status_code, (200, 302), msg=f"{url} -> {response.status_code}")
        return response

    def test_todas_las_paginas_principales(self):
        urls = [
            reverse("dashboard:inicio"),
            reverse("produccion:lista"),
            reverse("produccion:registrar"),
            reverse("produccion:detalle_produccion", args=[self.produccion.id]),
            reverse("produccion:buscar_codigo"),
            reverse("produccion:buscar_codigo") + "?codigo=" + self.detalle.pacas.first().codigo_unico,
            reverse("produccion:ficha_paca", args=[self.detalle.pacas.first().codigo_unico]),
            reverse("ficha_paca_corta", args=[self.detalle.pacas.first().codigo_unico]),
            reverse("produccion:etiquetas", args=[self.produccion.id]),
            reverse("clientes:lista_clientes"),
            reverse("clientes:crear_cliente"),
            reverse("clientes:editar_cliente", args=[self.cliente.id]),
            reverse("proveedores:lista_proveedores"),
            reverse("proveedores:crear_proveedor"),
            reverse("proveedores:editar_proveedor", args=[self.proveedor.id]),
            reverse("proveedores:lista_ingresos"),
            reverse("proveedores:crear_ingreso"),
            reverse("transportes:lista_transportes"),
            reverse("transportes:crear_transporte"),
            reverse("transportes:editar_transporte", args=[self.transporte.id]),
            reverse("ventas:lista_ventas"),
            reverse("ventas:crear_venta"),
            reverse("despachos:lista"),
            reverse("despachos:crear"),
            reverse("despachos:ver", args=[self.despacho.id]),
            reverse("despachos:editar", args=[self.despacho.id]),
            reverse("inventario:dashboard"),
            reverse("analytics:panel"),
            reverse("reportes:panel"),
            reverse("reportes:clientes"),
            reverse("reportes:proveedores"),
            reverse("reportes:transportes"),
            reverse("reportes:materia_prima"),
            reverse("reportes:reporte_produccion"),
            reverse("reportes:ventas"),
            reverse("reportes:despachos"),
            reverse("reportes:reporte_usuarios"),
            reverse("lista_usuarios"),
            reverse("registrar_usuario"),
            reverse("editar_usuario", args=[PerfilUsuario.objects.get(usuario=self.user).id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self._get(url)

    def test_excels(self):
        urls = [
            reverse("reportes:exportar_clientes_excel"),
            reverse("reportes:exportar_proveedores_excel"),
            reverse("reportes:exportar_transportes_excel"),
            reverse("reportes:exportar_materia_prima_excel"),
            reverse("reportes:exportar_produccion_excel"),
            reverse("reportes:exportar_ventas_excel"),
            reverse("reportes:exportar_despachos_excel"),
            reverse("reportes:exportar_usuarios_excel"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_ficha_publica_paca(self):
        paca = self.detalle.pacas.first()
        self.client.logout()
        response = self.client.get(
            reverse("produccion:ficha_paca", args=[paca.codigo_unico])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, paca.codigo_unico)
        self.assertContains(response, "Fecha y hora de elaboración")

    def test_qr_apunta_a_ficha_publica(self):
        paca = self.detalle.pacas.first()
        with self.settings(SITE_URL=""):
            with patch(
                "apps.produccion.labels.generar_qr_svg", return_value=b"<svg/>"
            ) as qr:
                preparar_etiquetas([paca], base_url="https://velpack.example")
        texto_qr = qr.call_args.args[0]
        self.assertIn(f"https://velpack.example/p/{paca.codigo_unico}/", texto_qr)
        self.assertIn(paca.codigo_unico, texto_qr)
        self.assertIn("Elaborado:", texto_qr)
        self.assertIn(self.producto.nombre, texto_qr)

    def test_terminal_operador(self):
        self.client.logout()
        self.client.post(reverse("operadores:login_operador"), {"cedula": "0102030405"})
        response = self.client.get(reverse("operadores:terminal_operador"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("operadores:etiquetas"))
        self.assertEqual(response.status_code, 200)

    def test_terminal_guarda_e_imprime_sin_redirigir(self):
        self.client.logout()
        self.client.post(reverse("operadores:login_operador"), {"cedula": "0102030405"})
        self.client.post(
            reverse("operadores:terminal_operador"),
            {"accion": "configurar_color", "color_id": self.color.id},
        )
        response = self.client.post(
            reverse("operadores:terminal_operador"),
            {
                "accion": "registrar",
                "producto_id": self.producto.id,
                "cantidad_pacas": "2",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="marco-impresion"')
        self.assertContains(response, "se imprimirán automáticamente")

    def test_flujos_post(self):
        # Cliente
        response = self.client.post(
            reverse("clientes:crear_cliente"),
            {
                "nombre": "Cliente Nuevo",
                "ruc": "0102030405999",
                "telefono": "0999999999",
                "correo": "nuevo@example.com",
                "direccion": "Direccion",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Proveedor
        response = self.client.post(
            reverse("proveedores:crear_proveedor"),
            {
                "nombre": "Proveedor Nuevo",
                "ruc": "0102030405888",
                "telefono": "0999999999",
                "correo": "provnuevo@example.com",
                "direccion": "Direccion",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Transporte
        response = self.client.post(
            reverse("transportes:crear_transporte"),
            {
                "placa": "XYZ9999",
                "identificacion": "0102030405",
                "propietario": "Propietario",
                "conductor": "Conductor",
                "telefono": "0999999999",
                "capacidad_kg": "1000",
                "observacion": "",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Materia prima
        response = self.client.post(
            reverse("proveedores:crear_ingreso"),
            {
                "proveedor": self.proveedor.id,
                "tipo_material": "CARTON",
                "peso_cargado": "100",
                "peso_vacio": "10",
                "cantidad": "0",
                "observacion": "Prueba",
            },
        )
        self.assertEqual(response.status_code, 302)

        # Despacho con formset
        response = self.client.post(
            reverse("despachos:crear"),
            {
                "cliente": self.cliente.id,
                "transporte": self.transporte.id,
                "numero_guia": "GUIA-NUEVA",
                "fecha": timezone.localdate().isoformat(),
                "direccion_entrega": "Direccion",
                "estado": "PENDIENTE",
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
        self.assertEqual(response.status_code, 302)

        # Venta
        response = self.client.post(
            reverse("ventas:crear_venta"),
            {
                "numero_factura": "FAC-NUEVA",
                "cliente": self.cliente.id,
                "observacion": "Prueba",
                "metodo_pago": "efectivo",
                "estado_pago": "pendiente",
                "modelo[]": [self.producto.id],
                "color[]": [self.color.id],
                "cantidad[]": ["1"],
                "precio[]": ["15.00"],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Venta.objects.filter(numero_factura="FAC-NUEVA").exists())

        # Actualizar pago
        response = self.client.post(
            reverse("ventas:actualizar_estado_pago", args=[self.venta.id]),
            {"metodo_pago": "transferencia", "estado_pago": "pagado"},
        )
        self.assertEqual(response.status_code, 302)

        # Cronograma
        response = self.client.post(
            reverse("produccion:registrar"),
            {"productos_activos[]": [self.producto.id]},
        )
        self.assertEqual(response.status_code, 302)

        # Marcar despacho entregado
        response = self.client.post(reverse("despachos:entregar", args=[self.despacho.id]))
        self.assertEqual(response.status_code, 302)

        # Usuarios y operadores
        response = self.client.post(
            reverse("registrar_usuario"),
            {
                "rol": "operador",
                "first_name": "Operador",
                "last_name": "Nuevo",
                "cedula": "0999999999",
            },
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            reverse("registrar_usuario"),
            {
                "rol": "usuario",
                "username": "usuario_nuevo",
                "password": "ClaveSegura123",
                "email": "usuario@example.com",
                "first_name": "Usuario",
                "last_name": "Nuevo",
            },
        )
        self.assertEqual(response.status_code, 302)

        usuario_nuevo = PerfilUsuario.objects.get(usuario__username="usuario_nuevo")
        response = self.client.post(
            reverse("editar_usuario", args=[usuario_nuevo.usuario_id]),
            {
                "username": "usuario_nuevo",
                "email": "usuario2@example.com",
                "first_name": "Usuario",
                "last_name": "Editado",
                "rol": "usuario",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)

        operador_nuevo = Operador.objects.get(cedula="0999999999")
        response = self.client.post(
            reverse("editar_operador", args=[operador_nuevo.id]),
            {
                "first_name": "Operador",
                "last_name": "Editado",
                "cedula": "0999999999",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
