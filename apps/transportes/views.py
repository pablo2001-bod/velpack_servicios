from django.shortcuts import render, redirect, get_object_or_404
from .models import Transporte
from .forms import TransporteForm
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def lista_transportes(request):
    transportes = Transporte.objects.all()
    return render(request, 'transportes/lista_transportes.html', {'transportes': transportes})

@staff_member_required
def crear_transporte(request):
    if request.method == 'POST':
        form = TransporteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('transportes:lista_transportes')
    else:
        form = TransporteForm()
    return render(request, 'transportes/form_transporte.html', {'form': form})

@staff_member_required
def editar_transporte(request, pk):
    transporte = get_object_or_404(Transporte, pk=pk)
    if request.method == 'POST':
        form = TransporteForm(request.POST, instance=transporte)
        if form.is_valid():
            form.save()
            return redirect('transportes:lista_transportes')
    else:
        form = TransporteForm(instance=transporte)
    return render(request, 'transportes/form_transporte.html', {'form': form})

@staff_member_required
def eliminar_transporte(request, pk):
    if request.method == 'POST':
        transporte = get_object_or_404(Transporte, pk=pk)
        transporte.delete()
    return redirect('transportes:lista_transportes')