from django import forms
from .models import Transporte

class TransporteForm(forms.ModelForm):
    class Meta:
        model = Transporte
        fields = [
            'placa', 
            'identificacion', 
            'propietario', 
            'conductor', 
            'telefono', 
            'capacidad_kg', 
            'observacion', 
            'activo'
        ]
        widgets = {
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'propietario': forms.TextInput(attrs={'class': 'form-control'}),
            'conductor': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidad_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }