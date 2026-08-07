from django import forms
from .models import Despacho, DetalleDespacho

class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = ['cliente', 'transporte', 'numero_guia', 'fecha', 'direccion_entrega', 'estado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'transporte': forms.Select(attrs={'class': 'form-control'}),
            'numero_guia': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_entrega': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

class DetalleDespachoForm(forms.ModelForm):
    class Meta:
        model = DetalleDespacho
        fields = ['cantidad', 'precio', 'variedad', 'color']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control cantidad'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control precio'}),
            'variedad': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-control'}),
        }