from django import forms

from .models import Produccion, DetalleProduccion


class ProduccionForm(forms.ModelForm):

    class Meta:
        model = Produccion

        fields = [
            "fecha",
            "operador",
            "observacion",
        ]

        widgets = {

            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "operador": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "observacion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),

        }


class DetalleProduccionForm(forms.ModelForm):

    class Meta:
        model = DetalleProduccion

        fields = [
            "producto",
            "color",
            "cantidad_pacas",
        ]

        widgets = {

            "producto": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "color": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "cantidad_pacas": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

        }