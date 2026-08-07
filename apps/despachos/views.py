from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import Despacho, DetalleDespacho
from .forms import DespachoForm

# Definimos el formset vinculando el modelo principal y el detalle
DetalleFormSet = inlineformset_factory(
    Despacho, DetalleDespacho, 
    fields=('cantidad', 'precio', 'variedad', 'color'), 
    extra=1, 
    can_delete=True
)

def lista_despacho(request):
    query = request.GET.get('q', '')
    # Traemos los despachos optimizando la consulta de sus detalles, productos y colores
    despachos = Despacho.objects.prefetch_related('detalles__variedad', 'detalles__color').all()
    
    if query:
        despachos = despachos.filter(cliente__identificacion__icontains=query)
    
    pendientes = despachos.filter(estado='PENDIENTE')
    entregados = despachos.filter(estado='ENTREGADO')
    
    return render(request, 'despachos/lista_despacho.html', {
        'pendientes': pendientes,
        'entregados': entregados,
        'query': query
    })

def marcar_entregado(request, id):
    despacho = get_object_or_404(Despacho, id=id)
    despacho.estado = 'ENTREGADO'
    despacho.save()
    return redirect('despachos:lista')

def crear_despacho(request):
    if request.method == 'POST':
        form = DespachoForm(request.POST)
        detalle_formset = DetalleFormSet(request.POST)
        
        if form.is_valid() and detalle_formset.is_valid():
            despacho = form.save()
            detalle_formset.instance = despacho
            detalle_formset.save()
            return redirect('despachos:lista')
        else:
            # Imprime errores en la terminal si algo falla para que los veas
            print("Errores en Form Principal:", form.errors)
            print("Errores en Formset Detalles:", detalle_formset.errors)
    else:
        form = DespachoForm()
        detalle_formset = DetalleFormSet()
        
    # CORREGIDO: Apunta correctamente a 'form_despacho.html'
    return render(request, 'despachos/form_despacho.html', {
        'form': form, 
        'detalle_formset': detalle_formset, 
        'titulo': 'Nueva Guía'
    })

def editar_despacho(request, id):
    despacho = get_object_or_404(Despacho, id=id)
    if request.method == 'POST':
        form = DespachoForm(request.POST, instance=despacho)
        detalle_formset = DetalleFormSet(request.POST, instance=despacho)
        
        if form.is_valid() and detalle_formset.is_valid():
            form.save()
            detalle_formset.save()
            return redirect('despachos:lista')
        else:
            print("Errores en Edición Form:", form.errors)
            print("Errores en Edición Detalles:", detalle_formset.errors)
    else:
        form = DespachoForm(instance=despacho)
        detalle_formset = DetalleFormSet(instance=despacho)
        
    return render(request, 'despachos/form_despacho.html', {
        'form': form, 
        'detalle_formset': detalle_formset, 
        'titulo': 'Editar Guía'
    })

def ver_despacho(request, id):
    despacho = get_object_or_404(Despacho, id=id)
    return render(request, 'despachos/ver_despacho.html', {
        'despacho': despacho,
        'titulo': f'Detalle Guía {despacho.numero_guia}'
    })

def imprimir_despacho(request, id):
    despacho = get_object_or_404(Despacho, id=id)
    return render(request, 'despachos/imprimir.html', {
        'despacho': despacho,
        'titulo': f'Imprimir Guía {despacho.numero_guia}'
    })