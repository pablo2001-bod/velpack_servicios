from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import PerfilUsuario
from apps.produccion.models import Operador, Turno


class PerfilUsuarioTests(TestCase):
    def test_obtener_o_crear_genera_codigo_y_reutiliza_perfil(self):
        usuario = User.objects.create_user(username="ana", password="clave-segura")

        perfil = PerfilUsuario.obtener_o_crear_para(usuario)
        mismo_perfil = PerfilUsuario.obtener_o_crear_para(usuario)

        self.assertEqual(perfil.pk, mismo_perfil.pk)
        self.assertEqual(perfil.codigo_operador, "ANA")

    def test_codigos_de_operador_son_unicos(self):
        usuario_1 = User.objects.create_user(username="ana", password="clave-segura")
        usuario_2 = User.objects.create_user(username="ana2", password="clave-segura")

        perfil_1 = PerfilUsuario.obtener_o_crear_para(usuario_1)
        perfil_2 = PerfilUsuario.obtener_o_crear_para(usuario_2)

        self.assertNotEqual(perfil_1.codigo_operador, perfil_2.codigo_operador)


class SeguridadYAvisosTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="ClaveAdmin123!"
        )
        self.client.force_login(self.admin)

    def test_registro_rechaza_clave_debil(self):
        response = self.client.post(
            reverse("registrar_usuario"),
            {
                "rol": "superusuario",
                "username": "nuevo",
                "email": "nuevo@example.com",
                "password": "12345678",
            },
        )

        self.assertRedirects(response, reverse("registrar_usuario"))
        self.assertFalse(User.objects.filter(username="nuevo").exists())

    def test_registro_acepta_clave_fuerte(self):
        response = self.client.post(
            reverse("registrar_usuario"),
            {
                "rol": "usuario_normal",
                "username": "nuevo",
                "email": "nuevo@example.com",
                "password": "ClaveSegura123!",
            },
        )

        self.assertRedirects(response, reverse("lista_usuarios"))
        self.assertTrue(User.objects.filter(username="nuevo").exists())
        self.assertTrue(User.objects.get(username="nuevo").is_staff)

    def test_registro_como_administrador_no_crea_superusuario(self):
        response = self.client.post(
            reverse("registrar_usuario"),
            {
                "rol": "superusuario",
                "username": "admin2",
                "email": "admin2@example.com",
                "password": "ClaveSegura123!",
            },
        )

        self.assertRedirects(response, reverse("lista_usuarios"))
        usuario = User.objects.get(username="admin2")
        self.assertTrue(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_editar_no_promueve_a_superusuario(self):
        usuario = User.objects.create_user(
            username="admin3", password="ClaveSegura123!", is_staff=True
        )

        response = self.client.post(
            reverse("editar_usuario", args=[usuario.id]),
            {
                "username": "admin3",
                "email": "admin3@example.com",
                "rol": "superusuario",
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("lista_usuarios"))
        usuario.refresh_from_db()
        self.assertTrue(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

class TurnosAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="ClaveAdmin123!"
        )
        self.client.force_login(self.admin)

    def test_crear_editar_y_eliminar_turno(self):
        response = self.client.post(
            reverse("crear_turno"),
            {
                "nombre": "Tarde",
                "hora_inicio": "15:00",
                "hora_fin": "23:00",
                "activo": "on",
            },
        )
        self.assertRedirects(response, reverse("lista_usuarios"))
        turno = Turno.objects.get(nombre="Tarde")

        response = self.client.post(
            reverse("editar_turno", args=[turno.id]),
            {
                "nombre": "Tarde",
                "hora_inicio": "14:00",
                "hora_fin": "22:00",
                "activo": "on",
            },
        )
        self.assertRedirects(response, reverse("lista_usuarios"))
        turno.refresh_from_db()
        self.assertEqual(turno.hora_inicio.strftime("%H:%M"), "14:00")

        response = self.client.post(reverse("eliminar_turno", args=[turno.id]))
        self.assertRedirects(response, reverse("lista_usuarios"))
        self.assertFalse(Turno.objects.filter(pk=turno.id).exists())

    def test_turno_no_superusuario_no_puede_gestionar(self):
        usuario = User.objects.create_user(username="normal", password="ClaveNormal123!")
        self.client.force_login(usuario)

        response = self.client.get(reverse("crear_turno"))

        self.assertEqual(response.status_code, 302)


class ValidacionesYSeguridadTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="ClaveAdmin123!"
        )
        self.client.force_login(self.admin)

    def test_registro_no_repite_mensajes_de_clave(self):
        response = self.client.post(
            reverse("registrar_usuario"),
            {
                "rol": "usuario_normal",
                "username": "nuevo",
                "email": "nuevo@example.com",
                "password": "nuevo",
            },
            follow=True,
        )
        contenido = response.content.decode()

        self.assertEqual(
            contenido.count("La contraseña es demasiado similar a la de nombre de usuario."),
            1,
        )
        self.assertEqual(
            contenido.count(
                "La contraseña es demasiado corta. Debe contener por lo menos 8 caracteres."
            ),
            1,
        )
        self.assertContains(response, "Mínimo 8 caracteres")

    def test_registro_rechaza_rol_invalido(self):
        response = self.client.post(
            reverse("registrar_usuario"),
            {
                "rol": "invalido",
                "username": "nuevo",
                "email": "nuevo@example.com",
                "password": "ClaveSegura123!",
            },
        )

        self.assertRedirects(response, reverse("registrar_usuario"))
        self.assertFalse(User.objects.filter(username="nuevo").exists())

    def test_get_no_realiza_acciones_de_cambio(self):
        otro_usuario = User.objects.create_user(
            username="otro", password="ClaveSegura123!"
        )
        operador = Operador.objects.create(
            nombre_completo="Operador Prueba", cedula="0999999999"
        )
        turno = Turno.objects.create(
            nombre="Prueba", hora_inicio="00:00", hora_fin="23:59"
        )

        urls = [
            reverse("eliminar_operador", args=[operador.id]),
            reverse("eliminar_usuario", args=[otro_usuario.id]),
            reverse("eliminar_turno", args=[turno.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

    def test_no_puede_desactivar_al_ultimo_admin(self):
        response = self.client.post(
            reverse("editar_usuario", args=[self.admin.id]),
            {
                "username": "admin",
                "email": "admin@example.com",
                "rol": "usuario_normal",
            },
        )

        self.assertRedirects(response, reverse("editar_usuario", args=[self.admin.id]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser)
