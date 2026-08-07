from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q  # Necesario para el buscador
from django.core.exceptions import ValidationError
from .models import Venta, DetalleVenta
from .forms import VentaForm
from apps.accounts.models import PerfilUsuario 
from apps.catalogos.models import Producto, Color

@staff_member_required
def lista_ventas(request):
    # Ordenamos por -id para que el último registrado sea el primero
    ventas = Venta.objects.all().order_by('-id')
    
    # Lógica de búsqueda por RUC, nombre o factura
    query = request.GET.get('q')
    if query:
        ventas = ventas.filter(
            Q(cliente__ruc__icontains=query) | 
            Q(cliente__nombre__icontains=query) |
            Q(numero_factura__icontains=query)
        )
        
    return render(request, 'ventas/lista_ventas.html', {'ventas': ventas, 'query': query})

@staff_member_required
def crear_venta(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
                
                venta = Venta.objects.create(
                    numero_factura=request.POST.get('numero_factura'),
                    cliente_id=request.POST.get('cliente'),
                    usuario=perfil,
                    observacion=request.POST.get('observacion', '')
                )
                
                modelos = request.POST.getlist('modelo[]')
                colores = request.POST.getlist('color[]')
                cantidades = request.POST.getlist('cantidad[]')
                precios = request.POST.getlist('precio[]')
                
                for i in range(len(modelos)):
                    DetalleVenta.objects.create(
                        venta=venta,
                        modelo_id=modelos[i], 
                        color_id=colores[i],
                        cantidad_pacas=int(cantidades[i]),
                        precio_unitario=float(precios[i]),
                        subtotal=float(cantidades[i]) * float(precios[i])
                    )
            
            messages.success(request, "Venta registrada exitosamente.")
            return redirect('ventas:lista_ventas')

        except ValidationError as e:
            messages.error(request, f"Error de stock: {e.messages[0]}")
        except Exception as e:
            messages.error(request, "Ocurrió un error al registrar la venta.")
        
        return redirect('ventas:crear_venta')

    else:
        form = VentaForm()
    
    return render(request, 'ventas/form_venta.html', {
        'form': form,
        'modelos': Producto.objects.all(),
        'colores': Color.objects.all()
    })