from django.contrib import admin
from .models import Despacho

@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = ("numero_guia", "cliente", "transporte", "estado", "fecha", )
    search_fields = ("numero_guia", "cliente__nombre") 
    list_filter = ("estado", "fecha")