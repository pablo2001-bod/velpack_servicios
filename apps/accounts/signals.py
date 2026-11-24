from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone

from .models import AvisoInterno


@receiver(user_logged_in)
def avisar_ingreso_usuario(sender, request, user, **kwargs):
    AvisoInterno.objects.create(
        tipo="ingreso_usuario",
        titulo=f"Ingreso de usuario: {user.get_username()}",
        mensaje=(
            f"{user.get_full_name() or user.get_username()} inició sesión en el "
            f"sistema el {timezone.localtime():%d/%m/%Y a las %H:%M}."
        ),
        usuario=user,
    )
