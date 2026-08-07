from django.db import models


class Transporte(models.Model):

    placa = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Placa"
    )

    identificacion = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        verbose_name="Identificación / Cédula"
    )

    propietario = models.CharField(
        max_length=120,
        verbose_name="Propietario"
    )

    conductor = models.CharField(
        max_length=120,
        verbose_name="Conductor"
    )

    telefono = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="Teléfono"
    )

    capacidad_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Capacidad (Kg)"
    )

    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    activo = models.BooleanField(default=True)

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Transporte"
        verbose_name_plural = "Transportes"
        ordering = ["placa"]

    def __str__(self):
        return f"{self.placa} - {self.conductor}"