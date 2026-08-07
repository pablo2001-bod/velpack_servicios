from django.db import models


class Proveedor(models.Model):

    nombre = models.CharField(max_length=150)

    ruc = models.CharField(
        max_length=13,
        unique=True
    )

    telefono = models.CharField(
        max_length=15,
        blank=True
    )

    direccion = models.TextField()

    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class IngresoMateriaPrima(models.Model):

    TIPOS = [
        ("CARTON", "Cartón"),
        ("DUPLEX", "Duplex"),
        ("TINTE_MORADO", "Tinte Morado (1 Tonelada = 1000 kg)"),
        ("TINTE_VERDE", "Tinte Verde (1 Tonelada = 1000 kg)"),
        ("TINTE_AMARILLO", "Tinte Amarillo (Sacos de 25 kg)"),
        ("TINTE_ROJO", "Tinte Rojo (Sacos de 25 kg)"),
        ("OTRO", "Otro"),
    ]

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT
    )

    tipo_material = models.CharField(
        max_length=30,
        choices=TIPOS
    )

    # La fecha se guarda sola de forma automática
    fecha = models.DateField(auto_now_add=True)

    peso_cargado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True, null=True
    )

    peso_vacio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True, null=True
    )

    peso_neto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=0
    )

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True, null=True
    )

    observacion = models.TextField(
        blank=True
    )

    def save(self, *args, **kwargs):
        # Aseguramos valores numéricos para evitar errores de cálculo
        self.peso_cargado = self.peso_cargado or 0
        self.peso_vacio = self.peso_vacio or 0
        self.cantidad = self.cantidad or 0

        if self.tipo_material in ["CARTON", "DUPLEX"]:
            self.peso_neto = self.peso_cargado - self.peso_vacio
            self.cantidad = 0 # No usa cantidad por unidades
            
        elif self.tipo_material in ["TINTE_MORADO", "TINTE_VERDE"]:
            self.peso_neto = self.cantidad * 1000
            self.peso_cargado = 0
            self.peso_vacio = 0
            
        elif self.tipo_material in ["TINTE_AMARILLO", "TINTE_ROJO"]:
            self.peso_neto = self.cantidad * 25
            self.peso_cargado = 0
            self.peso_vacio = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_material_display()} - {self.peso_neto} kg ({self.proveedor.nombre})"