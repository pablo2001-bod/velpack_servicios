from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'ruc', 'telefono', 'correo', 'direccion', 'activo']
        # Usamos clases de Bootstrap (asumo que usas Bootstrap por el estilo de tus otras apps)
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }