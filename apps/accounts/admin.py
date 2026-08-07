from django.contrib import admin
from .models import Rol, PerfilUsuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
    )

    search_fields = (
        "nombre",
    )


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):

    list_display = (
        "usuario",
        "codigo_operador",
        "cargo",
        "activo",
    )

    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "codigo_operador",
    )

    list_filter = (
        "activo",
        "rol",
    )