from django import forms

from apps.produccion.models import Turno


class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ["nombre", "hora_inicio", "hora_fin", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "hora_inicio": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        datos = super().clean()
        inicio = datos.get("hora_inicio")
        fin = datos.get("hora_fin")
        if inicio and fin and inicio == fin:
            self.add_error("hora_fin", "La hora de fin debe ser distinta de la de inicio.")
            return datos

        for otro in Turno.objects.filter(activo=True).exclude(pk=self.instance.pk):
            if self._solapa(inicio, fin, otro.hora_inicio, otro.hora_fin):
                self.add_error(
                    "nombre",
                    f"El horario se solapa con el turno '{otro.nombre}' "
                    f"({otro.hora_inicio:%H:%M} - {otro.hora_fin:%H:%M}).",
                )
                break
        return datos

    @staticmethod
    def _solapa(inicio, fin, otro_inicio, otro_fin):
        if not all((inicio, fin, otro_inicio, otro_fin)):
            return False
        if otro_inicio <= otro_fin:
            return inicio < otro_fin and fin > otro_inicio
        return inicio < otro_fin or fin > otro_inicio
