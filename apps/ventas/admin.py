from django.contrib import admin

from .models import DetalleVenta, Venta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("numero_factura", "cliente", "fecha", "total", "estado_pago", "usuario")
    search_fields = ("numero_factura", "cliente__nombre", "cliente__ruc")
    list_filter = ("fecha", "estado_pago", "metodo_pago")
    readonly_fields = ("usuario", "total")
    inlines = (DetalleVentaInline,)