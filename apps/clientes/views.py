from django.shortcuts import render, redirect
from .models import Cliente
from .forms import ClienteForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente
from .forms import ClienteForm
from django.contrib.admin.views.decorators import staff_member_required

def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/lista_clientes.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clientes:lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/form_cliente.html', {'form': form})


@staff_member_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('clientes:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/form_cliente.html', {'form': form, 'editar': True})

@staff_member_required
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
    return redirect('clientes:lista_clientes')