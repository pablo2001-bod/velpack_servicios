from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from apps.catalogos.models import Color, Producto

from .models import (
    ConfiguracionProduccion,
    DetalleProduccion,
    Operador,
    ParametroProduccion,
    Produccion,
    TIPOS_INSUMO_PRODUCCION_AGRUPADOS,
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
    hex_color = forms.RegexField(
        regex=r"^#[0-9A-Fa-f]{6}$",
        required=False,
        widget=forms.TextInput(
            attrs={"type": "color", "class": "form-control form-control-color"}
        ),
    )

    class Meta:
        model = Color
        fields = ["nombre", "codigo", "hex_color", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(
                attrs={"class": "form-control", "maxlength": 1}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_codigo(self):
        return (self.cleaned_data["codigo"] or "").strip().upper()

    def clean_hex_color(self):
        return (self.cleaned_data.get("hex_color") or "#2e7d32").strip()


class ConfiguracionProduccionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionProduccion
        fields = ["pacas_por_lote"]
        widgets = {
            "pacas_por_lote": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
        }


class ParametroColorForm(forms.Form):
    color = forms.ModelChoiceField(
        queryset=Color.objects.all().order_by("nombre"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Color a producir",
    )
    activo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Parámetros activos",
    )


class ParametroInsumoForm(forms.Form):
    tipo_material = forms.ChoiceField(
        choices=TIPOS_INSUMO_PRODUCCION_AGRUPADOS,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Material o insumo",
    )
    cantidad_por_paca = forms.DecimalField(
        min_value=Decimal("0.001"),
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": "0.001", "step": "0.001"}
        ),
        label="Kg por paca",
    )
    activo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Activo",
    )


class BaseParametrosInsumosFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()
        tipos = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            tipo = form.cleaned_data.get("tipo_material")
            if not tipo:
                continue
            if tipo in tipos:
                form.add_error(
                    "tipo_material", "Este insumo ya está cargado para el color."
                )
            tipos.add(tipo)


ParametrosInsumosFormSet = forms.formset_factory(
    ParametroInsumoForm,
    formset=BaseParametrosInsumosFormSet,
    extra=4,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


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