from decimal import Decimal

from django import forms
from .models import Proveedor, IngresoMateriaPrima

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "ruc", "telefono", "correo", "direccion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "ruc": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class IngresoMateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = IngresoMateriaPrima
        fields = ['proveedor', 'tipo_material', 'peso_cargado', 'peso_vacio', 'cantidad', 'observacion']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'tipo_material': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_material'}),
            'peso_cargado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'peso_vacio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        datos = super().clean()
        tipo = datos.get("tipo_material")
        cargado = datos.get("peso_cargado") or Decimal("0")
        vacio = datos.get("peso_vacio") or Decimal("0")
        cantidad = datos.get("cantidad") or Decimal("0")

        if cargado < 0 or vacio < 0 or cantidad < 0:
            raise forms.ValidationError("Los pesos y la cantidad no pueden ser negativos.")

        if tipo in ["CARTON", "DUPLEX"] and vacio > cargado:
            raise forms.ValidationError(
                "El peso vacío no puede ser mayor que el peso cargado."
            )

        if tipo and tipo.startswith("TINTE_") and cantidad <= 0:
            raise forms.ValidationError(
                "La cantidad de tintes debe ser mayor que cero."
            )

        return datos