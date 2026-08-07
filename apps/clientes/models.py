from django.db import models


class Cliente(models.Model):

    nombre = models.CharField(max_length=150)

    ruc = models.CharField(
        max_length=13,
        unique=True
    )

    telefono = models.CharField(
        max_length=15,
        blank=True
    )

    correo = models.EmailField(
        blank=True
    )

    direccion = models.TextField()

    activo = models.BooleanField(default=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre