from django import forms
from .models import Despacho, DetalleDespacho

class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = [
            'cliente', 'transporte', 'numero_guia', 'fecha', 'direccion_entrega', 'estado',
            'ruc_emisor', 'direccion_emisor', 'ciudad_emisor', 'contribuyente',
            'agente_retencion', 'ambiente', 'emision', 'punto_partida',
            'estado_transporte', 'motivo', 'ruta', 'correo_empresa', 'telefono_empresa',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'transporte': forms.Select(attrs={'class': 'form-control'}),
            'numero_guia': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_entrega': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'ruc_emisor': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_emisor': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad_emisor': forms.TextInput(attrs={'class': 'form-control'}),
            'contribuyente': forms.TextInput(attrs={'class': 'form-control'}),
            'agente_retencion': forms.TextInput(attrs={'class': 'form-control'}),
            'ambiente': forms.TextInput(attrs={'class': 'form-control'}),
            'emision': forms.TextInput(attrs={'class': 'form-control'}),
            'punto_partida': forms.TextInput(attrs={'class': 'form-control'}),
            'estado_transporte': forms.TextInput(attrs={'class': 'form-control'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'ruta': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_empresa': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono_empresa': forms.TextInput(attrs={'class': 'form-control'}),
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