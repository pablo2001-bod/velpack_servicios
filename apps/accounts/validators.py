import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ComplejidadPasswordValidator:
    """Exige mayúscula, minúscula, número y carácter especial."""

    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("La contraseña debe incluir al menos una letra mayúscula."),
                code="password_sin_mayuscula",
            )
        if not re.search(r"[a-z]", password):
            raise ValidationError(
                _("La contraseña debe incluir al menos una letra minúscula."),
                code="password_sin_minuscula",
            )
        if not re.search(r"\d", password):
            raise ValidationError(
                _("La contraseña debe incluir al menos un número."),
                code="password_sin_numero",
            )
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                _("La contraseña debe incluir al menos un carácter especial."),
                code="password_sin_especial",
            )

    def get_help_text(self):
        return _(
            "Debe tener al menos 8 caracteres e incluir mayúscula, minúscula, "
            "número y carácter especial."
        )
