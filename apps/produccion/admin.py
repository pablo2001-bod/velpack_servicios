from django.contrib import admin

from .models import (
    CronogramaDiario,
    DetalleProduccion,
    Operador,
    Paca,
    Produccion,
    Turno,
)


@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "cedula", "activo")
    search_fields = ("nombre_completo", "cedula")
    list_filter = ("activo",)
    ordering = ("nombre_completo",)


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "hora_inicio", "hora_fin", "activo")
    list_filter = ("activo",)


@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    list_display = ("fecha", "turno", "operador", "total_pacas")
    list_filter = ("fecha", "turno")
    search_fields = ("operador__nombre_completo", "operador__cedula")


@admin.register(DetalleProduccion)
class DetalleProduccionAdmin(admin.ModelAdmin):
    list_display = ("produccion", "producto", "color", "cantidad_pacas")
    list_filter = ("producto", "color")


@admin.register(Paca)
class PacaAdmin(admin.ModelAdmin):
    list_display = ("codigo_unico", "lote", "numero_paca", "detalle")
    search_fields = ("codigo_unico",)
    list_filter = ("lote",)


@admin.register(CronogramaDiario)
class CronogramaDiarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "producto", "activo")
    list_filter = ("fecha", "activo")
    search_fields = ("producto__nombre",)
