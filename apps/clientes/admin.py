from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "ruc",
        "telefono",
        "direccion",
        "activo",
    )

    search_fields = (
        "nombre",
        "ruc",
    )

    list_filter = (
        "activo",
    )

    ordering = (
        "nombre",
    )