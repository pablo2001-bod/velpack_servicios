from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Proveedor, IngresoMateriaPrima
from .forms import ProveedorForm, IngresoMateriaPrimaForm

# ==================== VISTAS DE PROVEEDORES ====================

@staff_member_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedores/lista_proveedores.html', {'proveedores': proveedores})

@staff_member_required
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('proveedores:lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'proveedores/form_proveedor.html', {'form': form})

@staff_member_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return redirect('proveedores:lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'proveedores/form_proveedor.html', {'form': form})

@staff_member_required
def eliminar_proveedor(request, pk):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=pk)
        proveedor.delete()
    return redirect('proveedores:lista_proveedores')


# ==================== VISTAS DE MATERIA PRIMA ====================

@staff_member_required
def lista_ingresos(request):
    query = request.GET.get('q', '')
    if query:
        # Filtra por nombre o ruc del proveedor ordenado del más reciente al más antiguo
        ingresos = IngresoMateriaPrima.objects.filter(
            proveedor__ruc__icontains=query
        ) | IngresoMateriaPrima.objects.filter(
            proveedor__nombre__icontains=query
        )
        ingresos = ingresos.order_by('-id')
    else:
        # El último ingresado aparece primero (-id)
        ingresos = IngresoMateriaPrima.objects.all().order_by('-id')
        
    return render(request, 'proveedores/listamateriap.html', {'ingresos': ingresos, 'query': query})

@staff_member_required
def crear_ingreso(request):
    if request.method == 'POST':
        form = IngresoMateriaPrimaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('proveedores:lista_ingresos')
    else:
        form = IngresoMateriaPrimaForm()
    return render(request, 'proveedores/form_ingreso.html', {'form': form})