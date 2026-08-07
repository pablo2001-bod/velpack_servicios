from django.contrib import admin
from .models import (
    Turno,
    Produccion,
    DetalleProduccion,
    Paca
)


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "hora_inicio",
        "hora_fin",
        "activo",
    )

    list_filter = (
        "activo",
    )


@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):

    list_display = (
        "fecha",
        "turno",
        "operador",
        "total_pacas",
    )

    list_filter = (
        "fecha",
        "turno",
    )

    search_fields = (
        "operador__usuario__first_name",
        "operador__usuario__last_name",
    )


@admin.register(DetalleProduccion)
class DetalleProduccionAdmin(admin.ModelAdmin):

    list_display = (
        "produccion",
        "producto",
        "color",
        "cantidad_pacas",
    )

    list_filter = (
        "producto",
        "color",
    )


@admin.register(Paca)
class PacaAdmin(admin.ModelAdmin):

    list_display = (
        "codigo_unico",
        "lote",
        "numero_paca",
        "detalle",
    )

    search_fields = (
        "codigo_unico",
    )

    list_filter = (
        "lote",
    )