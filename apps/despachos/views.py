from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DespachoForm
from .models import Despacho, DetalleDespacho

# Definimos el formset vinculando el modelo principal y el detalle
DetalleFormSet = inlineformset_factory(
    Despacho,
    DetalleDespacho,
    fields=("cantidad", "precio", "variedad", "color"),
    extra=1,
    can_delete=True,
)


@login_required
def lista_despacho(request):
    query = request.GET.get("q", "").strip()
    despachos = Despacho.objects.select_related("cliente", "transporte").prefetch_related(
        "detalles__variedad", "detalles__color"
    )

    if query:
        despachos = despachos.filter(
            Q(cliente__ruc__icontains=query)
            | Q(cliente__nombre__icontains=query)
            | Q(numero_guia__icontains=query)
        )

    return render(
        request,
        "despachos/lista_despacho.html",
        {
            "pendientes": despachos.filter(estado="PENDIENTE"),
            "entregados": despachos.filter(estado="ENTREGADO"),
            "query": query,
        },
    )


@login_required
def marcar_entregado(request, id):
    despacho = get_object_or_404(Despacho, id=id)
    despacho.estado = "ENTREGADO"
    despacho.save(update_fields=["estado"])
    messages.success(request, f"La guía {despacho.numero_guia} fue marcada como entregada.")
    return redirect("despachos:lista")


@login_required
def crear_despacho(request):
    if request.method == 'POST':
        form = DespachoForm(request.POST)
        detalle_formset = DetalleFormSet(request.POST)
        
        if form.is_valid() and detalle_formset.is_valid():
            despacho = form.save()
            detalle_formset.instance = despacho
            detalle_formset.save()
            messages.success(request, f"Guía {despacho.numero_guia} creada correctamente.")
            return redirect("despachos:lista")
        messages.error(request, "Revise los datos de la guía y de sus detalles.")
    else:
        form = DespachoForm()
        detalle_formset = DetalleFormSet()

    return render(
        request,
        "despachos/form_despacho.html",
        {
            "form": form,
            "detalle_formset": detalle_formset,
            "titulo": "Nueva Guía",
        },
    )


@login_required
def editar_despacho(request, id):
    despacho = get_object_or_404(Despacho, id=id)
    if request.method == 'POST':
        form = DespachoForm(request.POST, instance=despacho)
        detalle_formset = DetalleFormSet(request.POST, instance=despacho)
        
        if form.is_valid() and detalle_formset.is_valid():
            form.save()
            detalle_formset.save()
            messages.success(request, f"Guía {despacho.numero_guia} actualizada correctamente.")
            return redirect("despachos:lista")
        messages.error(request, "Revise los datos de la guía y de sus detalles.")
    else:
        form = DespachoForm(instance=despacho)
        detalle_formset = DetalleFormSet(instance=despacho)

    return render(
        request,
        "despachos/form_despacho.html",
        {
            "form": form,
            "detalle_formset": detalle_formset,
            "titulo": "Editar Guía",
        },
    )


@login_required
def ver_despacho(request, id):
    despacho = get_object_or_404(
        Despacho.objects.select_related("cliente", "transporte").prefetch_related(
            "detalles__variedad", "detalles__color"
        ),
        id=id,
    )
    return render(
        request,
        "despachos/ver_despacho.html",
        {
            "despacho": despacho,
            "titulo": f"Detalle Guía {despacho.numero_guia}",
        },
    )