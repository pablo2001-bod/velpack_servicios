from django.contrib import admin
from .models import Venta

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("numero_factura", "cliente", "fecha", "total", "usuario")
    search_fields = ("numero_factura", "cliente__nombre")
    list_filter = ("fecha",)
    readonly_fields = ("usuario",)