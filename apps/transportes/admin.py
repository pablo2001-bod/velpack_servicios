from django.contrib import admin
from .models import Transporte


@admin.register(Transporte)
class TransporteAdmin(admin.ModelAdmin):

    list_display = (
        "placa",
        "conductor",
        "propietario",
        "capacidad_kg",
        "activo",
    )

    search_fields = (
        "placa",
        "conductor",
    )

    list_filter = (
        "activo",
    )