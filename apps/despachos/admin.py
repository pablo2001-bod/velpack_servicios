from django.contrib import admin

from .models import Despacho, DetalleDespacho


class DetalleDespachoInline(admin.TabularInline):
    model = DetalleDespacho
    extra = 0


@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = ("numero_guia", "cliente", "transporte", "estado", "fecha")
    search_fields = ("numero_guia", "cliente__nombre", "cliente__ruc")
    list_filter = ("estado", "fecha")
    inlines = (DetalleDespachoInline,)