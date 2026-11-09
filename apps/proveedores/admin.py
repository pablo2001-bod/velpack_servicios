from django.contrib import admin
from .models import Proveedor, IngresoMateriaPrima


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "ruc",
        "telefono",
        "correo",
        "activo",
    )

    search_fields = (
        "nombre",
        "ruc",
        "correo",
    )

    list_filter = (
        "activo",
    )

    ordering = (
        "nombre",
    )


@admin.register(IngresoMateriaPrima)
class IngresoMateriaPrimaAdmin(admin.ModelAdmin):

    list_display = (
        "proveedor",
        "fecha",
        "tipo_material",
        "peso_neto",
    )

    list_filter = (
        "tipo_material",
        "fecha",
    )

    search_fields = (
        "proveedor__nombre",
    )