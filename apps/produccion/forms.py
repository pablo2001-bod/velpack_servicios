from django import forms

from apps.catalogos.models import Color, Producto

from .models import (
    ConfiguracionProduccion,
    DetalleProduccion,
    Operador,
    ParametroProduccion,
    Produccion,
)


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


class ModeloForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "codigo", "activo", "es_segunda"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(
                attrs={"class": "form-control", "maxlength": 1}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "es_segunda": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_codigo(self):
        return (self.cleaned_data["codigo"] or "").strip().upper()


class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ["nombre", "codigo", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(
                attrs={"class": "form-control", "maxlength": 1}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_codigo(self):
        return (self.cleaned_data["codigo"] or "").strip().upper()


class ConfiguracionProduccionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionProduccion
        fields = ["pacas_por_lote"]
        widgets = {
            "pacas_por_lote": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
        }


class ParametroProduccionForm(forms.ModelForm):
    class Meta:
        model = ParametroProduccion
        fields = ["color", "tipo_material", "cantidad_por_paca", "activo"]
        widgets = {
            "color": forms.Select(attrs={"class": "form-select"}),
            "tipo_material": forms.Select(attrs={"class": "form-select"}),
            "cantidad_por_paca": forms.NumberInput(
                attrs={"class": "form-control", "min": "0.001", "step": "0.001"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ItemProduccionForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Modelo",
    )
    color = forms.ModelChoiceField(
        queryset=Color.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Color",
    )
    cantidad_pacas = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        label="Cantidad de pacas",
    )


ItemsProduccionFormSet = forms.formset_factory(
    ItemProduccionForm,
    extra=1,
    min_num=1,
    validate_min=True,
)


class RegistroProduccionForm(forms.Form):
    operador = forms.ModelChoiceField(
        queryset=Operador.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Operador",
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        label="Observación",
    )