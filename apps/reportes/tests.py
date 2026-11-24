from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class FiltrosFechasReportesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_superuser(
            username="admin", password="ClaveAdmin123!"
        )
        self.client.force_login(self.usuario)

    def test_fecha_invalida_muestra_mensaje(self):
        response = self.client.get(
            reverse("reportes:ventas"), {"fecha_inicio": "no-es-fecha"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no tiene un formato válido")
