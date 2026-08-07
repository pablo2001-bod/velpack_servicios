from django.contrib import admin
from .models import Producto, Color


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "codigo",
        "activo",
    )

    search_fields = (
        "nombre",
        "codigo",
    )

    list_filter = (
        "activo",
    )

    ordering = (
        "nombre",
    )


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "codigo",
        "activo",
    )

    search_fields = (
        "nombre",
        "codigo",
    )

    list_filter = (
        "activo",
    )

    ordering = (
        "nombre",
    )