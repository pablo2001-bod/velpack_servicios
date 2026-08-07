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

    def __str__(self):
        return self.nombre


class Color(models.Model):

    nombre = models.CharField(max_length=30)

    codigo = models.CharField(
        max_length=1,
        unique=True
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre