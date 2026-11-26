from django.core.validators import RegexValidator
from django.db import models


class Producto(models.Model):

    MODELOS = [

        ("I", "Inicial"),

        ("M", "Mediana"),

        ("G", "Gruesa"),

        ("E", "Extragruesa"),

    ]

    nombre = models.CharField(max_length=40)

    codigo = models.CharField(
        max_length=1,
        unique=True
    )

    activo = models.BooleanField(default=True)

    es_segunda = models.BooleanField(
        default=False,
        verbose_name="Línea económica (segunda calidad)",
    )

    def __str__(self):
        return self.nombre


class Color(models.Model):

    nombre = models.CharField(max_length=30)

    codigo = models.CharField(
        max_length=1,
        unique=True
    )

    hex_color = models.CharField(
        max_length=7,
        default="#2e7d32",
        validators=[
            RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Ingrese un color hexadecimal válido.")
        ],
        verbose_name="Color en terminal",
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre