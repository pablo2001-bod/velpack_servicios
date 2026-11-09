from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import PerfilUsuario


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
