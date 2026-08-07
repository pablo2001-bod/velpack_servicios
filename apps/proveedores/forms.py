from django import forms
from .models import Proveedor, IngresoMateriaPrima

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'ruc', 'telefono', 'direccion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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