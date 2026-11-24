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

    ruc_emisor = models.CharField(max_length=20, default="0591746284001", verbose_name="R.U.C. emisor")
    direccion_emisor = models.CharField(
        max_length=255,
        default="Av. Eloy Alfaro y Los Molinos, Latacunga",
        verbose_name="Dirección del emisor",
    )
    ciudad_emisor = models.CharField(
        max_length=100, default="Latacunga - Ecuador", verbose_name="Ciudad del emisor"
    )
    contribuyente = models.CharField(
        max_length=100, default="Especial 011", verbose_name="Contribuyente"
    )
    agente_retencion = models.CharField(
        max_length=100, default="Resolución No. 1", verbose_name="Agente de retención"
    )
    ambiente = models.CharField(max_length=30, default="PRODUCCIÓN", verbose_name="Ambiente")
    emision = models.CharField(max_length=30, default="NORMAL", verbose_name="Emisión")
    punto_partida = models.CharField(
        max_length=100, default="LATACUNGA", verbose_name="Punto de partida"
    )
    estado_transporte = models.CharField(
        max_length=50, default="En tránsito", verbose_name="Estado impreso"
    )
    motivo = models.CharField(max_length=100, default="VENTA", verbose_name="Motivo")
    ruta = models.CharField(
        max_length=150, default="LATACUNGA - SALCEDO", verbose_name="Ruta"
    )
    correo_empresa = models.EmailField(
        blank=True, default="velpack.2021@gmail.com", verbose_name="Correo de la empresa"
    )
    telefono_empresa = models.CharField(
        max_length=30, default="03-2800-000", verbose_name="Teléfono de la empresa"
    )
    
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