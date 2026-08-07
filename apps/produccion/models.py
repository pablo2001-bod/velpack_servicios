from django.db import models
from apps.catalogos.models import Producto, Color

# Subimos la declaración de Operador arriba para poder referenciarlo en Produccion
class Operador(models.Model):
    nombre_completo = models.CharField(max_length=150, verbose_name="Nombre Completo")
    cedula = models.CharField(max_length=10, unique=True, verbose_name="Cédula")
    activo = models.BooleanField(default=True)

    def obtener_iniciales(self):
        partes = self.nombre_completo.strip().split()
        if len(partes) >= 2:
            return f"{partes[0][0]}{partes[1][0]}".upper()
        elif len(partes) == 1:
            return f"{partes[0][:2]}".upper()
        return "OP"

    def __str__(self):
        return f"{self.nombre_completo} ({self.obtener_iniciales()})"


class Turno(models.Model):
    nombre = models.CharField(
        max_length=50,
        unique=True
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"

    def __str__(self):
        return self.nombre


class Produccion(models.Model):
    fecha = models.DateField()

    turno = models.ForeignKey(
        Turno,
        on_delete=models.PROTECT,
        related_name="producciones"
    )

    # CORREGIDO: Ahora apunta directamente al modelo Operador que está arriba
    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name="producciones"
    )

    total_pacas = models.PositiveIntegerField(
        default=0,
        editable=False
    )

    observacion = models.TextField(
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Producción"
        verbose_name_plural = "Producciones"

    def __str__(self):
        return f"{self.fecha} - {self.operador}"

    def actualizar_total(self):
        total = sum(
            detalle.cantidad_pacas
            for detalle in self.detalles.all()
        )
        Produccion.objects.filter(pk=self.pk).update(
            total_pacas=total
        )


class DetalleProduccion(models.Model):
    produccion = models.ForeignKey(
        Produccion,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT
    )
    cantidad_pacas = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Detalle de Producción"
        verbose_name_plural = "Detalles de Producción"
        constraints = [
            models.UniqueConstraint(
                fields=["produccion", "producto", "color"],
                name="detalle_producto_color_unico"
            )
        ]

    def __str__(self):
        return f"{self.producto} - {self.color}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.produccion.actualizar_total()

    def delete(self, *args, **kwargs):
        produccion = self.produccion
        super().delete(*args, **kwargs)
        produccion.actualizar_total()


class Paca(models.Model):
    detalle = models.ForeignKey(
        DetalleProduccion,
        on_delete=models.CASCADE,
        related_name="pacas"
    )
    codigo_unico = models.CharField(
        max_length=30,
        unique=True
    )
    lote = models.PositiveIntegerField()
    numero_paca = models.PositiveIntegerField()
    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "lote",
            "numero_paca"
        ]
        verbose_name = "Paca"
        verbose_name_plural = "Pacas"
        constraints = [
            models.UniqueConstraint(
                fields=["detalle", "lote", "numero_paca"],
                name="lote_paca_unica"
            )
        ]

    def __str__(self):
        return self.codigo_unico