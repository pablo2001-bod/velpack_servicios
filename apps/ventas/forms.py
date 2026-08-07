from django import forms
from .models import Venta

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        # Solo incluimos los campos que pertenecen a la tabla Venta
        fields = ['numero_factura', 'cliente', 'observacion'] 
        widgets = {
            'numero_factura': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: FAC-001'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Alguna observación adicional...'
            }),
        }
        labels = {
            'numero_factura': 'Número de Factura',
            'cliente': 'Seleccionar Cliente',
            'observacion': 'Observaciones'
        }

    def __init__(self, *args, **kwargs):
        super(VentaForm, self).__init__(*args, **kwargs)
        # Opcional: Si quieres que todos los campos sean requeridos
        for field in self.fields.values():
            field.required = True