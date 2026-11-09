from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class PaginasPrincipalesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="clave-segura"
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_paginas_principales_responden_ok(self):
        nombres = [
            "dashboard:inicio",
            "inventario:dashboard",
            "analytics:panel",
            "produccion:lista",
            "produccion:registrar",
            "produccion:buscar_codigo",
            "clientes:lista_clientes",
            "proveedores:lista_proveedores",
            "proveedores:lista_ingresos",
            "transportes:lista_transportes",
            "ventas:lista_ventas",
            "despachos:lista",
            "reportes:panel",
        ]

        for nombre in nombres:
            with self.subTest(url=nombre):
                response = self.client.get(reverse(nombre))
                self.assertEqual(response.status_code, 200)
