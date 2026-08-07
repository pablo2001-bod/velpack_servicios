from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.clientes.models import Cliente
from apps.accounts.models import PerfilUsuario 
from apps.catalogos.models import Producto, Color
from apps.produccion.models import DetalleProduccion

class Venta(models.Model):
    numero_factura = models.CharField(max_length=25, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="ventas")
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.numero_factura} - {self.cliente.nombre}"

    def actualizar_total(self):
        """Calcula el total sumando los subtotales de los detalles asociados."""
        nuevo_total = sum(detalle.subtotal for detalle in self.detalles.all())
        Venta.objects.filter(pk=self.pk).update(total=nuevo_total)

    @property
    def total_pacas(self):
        """Suma la cantidad de pacas de todos los detalles asociados a esta venta."""
        return sum(detalle.cantidad_pacas for detalle in self.detalles.all())


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    modelo = models.ForeignKey(Producto, on_delete=models.PROTECT)
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    cantidad_pacas = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def obtener_stock_actual(self):
        """Suma todo lo producido y le resta todo lo vendido anteriormente."""
        total_producido = DetalleProduccion.objects.filter(
            producto=self.modelo, 
            color=self.color
        ).aggregate(total=Sum('cantidad_pacas'))['total'] or 0

        # Sumamos todas las ventas previas de este mismo producto y color
        ventas_previas = DetalleVenta.objects.filter(
            modelo=self.modelo, 
            color=self.color
        )
        
        # Si estamos editando un detalle existente, excluimos el registro actual
        if self.pk:
            ventas_previas = ventas_previas.exclude(pk=self.pk)

        total_vendido = ventas_previas.aggregate(total=Sum('cantidad_pacas'))['total'] or 0

        return max(0, total_producido - total_vendido)

    def clean(self):
        """Valida que exista stock suficiente sumando todas las producciones y restando las ventas."""
        if self.modelo_id and self.color_id and self.cantidad_pacas:
            stock_disponible = self.obtener_stock_actual()
            
            if self.cantidad_pacas > stock_disponible:
                raise ValidationError(
                    f"Stock insuficiente para {self.modelo} {self.color}. Disponibles: {stock_disponible}"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            # Guardamos el detalle de la venta
            super().save(*args, **kwargs)
            
            # Actualizamos el total acumulado de la factura
            self.venta.actualizar_total()