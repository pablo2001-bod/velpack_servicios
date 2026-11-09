from django.db import models
from django.utils import timezone

from apps.catalogos.models import Producto, Color


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

    def obtener_codigo_acceso(self):
        """Código que el operador usa para entrar a la terminal táctil."""
        ultimos_cedula = self.cedula[-4:] if len(self.cedula) >= 4 else self.cedula
        return f"{self.obtener_iniciales()}{ultimos_cedula}".upper()

    @classmethod
    def buscar_por_credencial(cls, ingreso):
        """Busca un operador activo por cédula o por código de acceso."""
        ingreso = (ingreso or "").strip()
        if not ingreso:
            return None

        operador = cls.objects.filter(cedula__iexact=ingreso, activo=True).first()
        if operador:
            return operador

        ingreso = ingreso.upper()
        for op in cls.objects.filter(activo=True):
            codigos = {op.cedula.upper(), op.obtener_codigo_acceso()}
            # Compatibilidad con el formato antiguo para nombres de una palabra.
            partes = op.nombre_completo.strip().split()
            if len(partes) == 1 and partes[0]:
                ultimos_cedula = op.cedula[-4:] if len(op.cedula) >= 4 else op.cedula
                codigos.add(f"{partes[0][0]}X{ultimos_cedula}".upper())

            if ingreso in codigos:
                return op
        return None

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


class CronogramaDiario(models.Model):
    fecha = models.DateField(default=timezone.localdate)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha", "producto__nombre"]
        verbose_name = "Cronograma Diario"
        verbose_name_plural = "Cronogramas Diarios"
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "producto"],
                name="cronograma_fecha_producto_unico",
            )
        ]

    def __str__(self):
        return f"Cronograma {self.fecha} - {self.producto}"