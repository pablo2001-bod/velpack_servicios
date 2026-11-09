from django.db import models
from django.contrib.auth.models import User

# 1. Creamos el modelo Rol que te faltaba
class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil"
    )
    codigo_operador = models.CharField(
        max_length=5,
        unique=True,
        help_text="Ejemplo: PT"
    )
    telefono = models.CharField(
        max_length=15,
        blank=True
    )
    activo = models.BooleanField(default=True)
    
    # 2. Agregamos los campos 'rol' y 'cargo' que pide tu admin.py
    rol = models.ForeignKey(
        Rol, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Rol"
    )
    cargo = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Cargo"
    )

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    @classmethod
    def obtener_o_crear_para(cls, usuario):
        """Devuelve el perfil del usuario generando un código único si no existe."""
        perfil = cls.objects.filter(usuario=usuario).first()
        if perfil:
            return perfil

        base = (
            "".join(c for c in (usuario.username or "USR") if c.isalnum()).upper()[:4]
            or "USR"
        )
        codigo = base
        contador = 1
        while cls.objects.filter(codigo_operador=codigo).exists():
            sufijo = str(contador)
            codigo = f"{base[: max(1, 5 - len(sufijo))]}{sufijo}"
            contador += 1

        return cls.objects.create(usuario=usuario, codigo_operador=codigo)

    def __str__(self):
        return f"{self.usuario.get_full_name()} ({self.codigo_operador})"