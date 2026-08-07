from django.db import models
from apps.clientes.models import Cliente
from apps.transportes.models import Transporte
from apps.catalogos.models import Producto, Color 

class Despacho(models.Model):
    ESTADOS = [("PENDIENTE", "Pendiente"), ("ENTREGADO", "Entregado")]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    transporte = models.ForeignKey(Transporte, on_delete=models.PROTECT)
    numero_guia = models.CharField(max_length=25, unique=True)
    fecha = models.DateField()
    direccion_entrega = models.TextField()
    estado = models.CharField(max_length=15, choices=ESTADOS, default="PENDIENTE")
    
    def __str__(self):
        return f"Guía {self.numero_guia}"

    # Método para calcular el total general de la guía (¡dentro de la clase!)
    def obtener_total(self):
        total = sum(detalle.cantidad * detalle.precio for detalle in self.detalles.all())
        return round(total, 2)

class DetalleDespacho(models.Model):
    despacho = models.ForeignKey(Despacho, related_name='detalles', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    variedad = models.ForeignKey(Producto, on_delete=models.PROTECT, verbose_name="Variedad")
    color = models.ForeignKey(Color, on_delete=models.PROTECT, verbose_name="Color")

    def __str__(self):
        return f"{self.cantidad} - {self.variedad.nombre}"