from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

from .forms import ProduccionForm
from .models import Produccion, DetalleProduccion, Paca, Operador, Turno
from apps.catalogos.models import Producto, Color

def lista_produccion(request):
    producciones = Produccion.objects.all()
    return render(
        request,
        "produccion/lista.html",
        {
            "producciones": producciones
        }
    )

def registrar_produccion(request):
    if request.method == "POST":
        post_data = request.POST.copy()
        operador_id = post_data.get('operador')
        turno_id = post_data.get('turno')
        
        fecha_actual_str = datetime.today().strftime('%Y-%m-%d')
        post_data['fecha'] = fecha_actual_str
        
        form = ProduccionForm(post_data)
        
        if 'operador' in form.errors: del form.errors['operador']
        if 'turno' in form.errors: del form.errors['turno']
        
        if form.is_valid() and operador_id and turno_id:
            try:
                with transaction.atomic():
                    produccion = form.save(commit=False)
                    produccion.fecha = datetime.today().date()
                    produccion.operador_id = int(operador_id)
                    produccion.turno_id = int(turno_id)
                    produccion.save()

                    productos_ids = request.POST.getlist('producto[]')
                    colores_ids = request.POST.getlist('color[]')
                    cantidades = request.POST.getlist('cantidad_pacas[]')

                    for i in range(len(productos_ids)):
                        prod_id = productos_ids[i]
                        col_id = colores_ids[i]
                        cant = int(cantidades[i])

                        if prod_id and col_id and cant > 0:
                            producto = Producto.objects.get(id=prod_id)
                            color = Color.objects.get(id=col_id)

                            detalle = DetalleProduccion.objects.create(
                                produccion=produccion,
                                producto=producto,
                                color=color,
                                cantidad_pacas=cant
                            )

                            # --- CONFIGURACIÓN DEL CÓDIGO ÚNICO ---
                            iniciales_op = produccion.operador.obtener_iniciales()
                            fecha_formateada = produccion.fecha.strftime('%d%m%y')
                            codigo_prod_col = f"{producto.codigo.strip().upper()}{color.codigo.strip().upper()}"
                            
                            # 1. Buscamos cómo quedó el último lote histórico para este Producto + Color
                            ultima_paca = Paca.objects.filter(
                                detalle__producto=producto,
                                detalle__color=color
                            ).order_by('-id').first()

                            # Verificamos si hay un lote sin completar (menos de 50 pacas)
                            if ultima_paca and ultima_paca.numero_paca < 50:
                                pacas_para_completar = 50 - ultima_paca.numero_paca
                                lote_heredado = ultima_paca.lote
                                paca_anterior_en_lote = ultima_paca.numero_paca
                            else:
                                pacas_para_completar = 0
                                lote_heredado = 0
                                paca_anterior_en_lote = 0

                            # 2. Generamos EXACTAMENTE 'cant' pacas (ej. 42)
                            for paca_contador in range(1, cant + 1):
                                
                                # CASO A: Completar el lote a medias del turno previo
                                if pacas_para_completar > 0 and paca_contador <= pacas_para_completar:
                                    num_lote = lote_heredado
                                    paca_en_lote = paca_anterior_en_lote + paca_contador
                                
                                # CASO B: Arrancar los lotes PROPIOS de este turno (Lote 1, Lote 2, etc.)
                                else:
                                    pacas_propias = paca_contador - pacas_para_completar
                                    num_lote = ((pacas_propias - 1) // 50) + 1
                                    paca_en_lote = ((pacas_propias - 1) % 50) + 1

                                lote_formateado = f"L{num_lote:02d}"
                                paca_formateada = f"{paca_en_lote:03d}"

                                nuevo_codigo_unico = f"{iniciales_op}{fecha_formateada}{codigo_prod_col}{paca_formateada}{lote_formateado}"

                                Paca.objects.create(
                                    detalle=detalle,
                                    numero_paca=paca_en_lote,
                                    lote=num_lote,
                                    codigo_unico=nuevo_codigo_unico
                                )

                    messages.success(request, "¡Producción y pacas guardadas correctamente!")
                    return redirect('produccion:lista')
                
            except Exception as e:
                messages.error(request, f"Ocurrió un error al guardar la producción: {str(e)}")
        else:
            messages.error(request, "Por favor, verifique que todos los campos estén correctos.")
    else:
        form = ProduccionForm()

    productos = Producto.objects.all()
    colores = Color.objects.all()
    operadores = Operador.objects.filter(activo=True)
    turnos = Turno.objects.filter(activo=True)

    return render(
        request, "produccion/registrar.html",
        {
            "form": form, "productos": productos, "colores": colores,
            "operadores": operadores, "turnos": turnos,
            "fecha_hoy": datetime.today().strftime('%Y-%m-%d')
        }
    )
    
def detalle_produccion(request, id):
    produccion = Produccion.objects.get(id=id)
    return render(
        request,
        "produccion/detalle.html",
        {
            "produccion": produccion
        }
    )
    
def buscar_codigo(request):
    codigo = request.GET.get('codigo', '').strip()
    paca = None
    error_mensaje = None

    if codigo:
        try:
            paca = Paca.objects.select_related(
                'detalle__produccion', 
                'detalle__producto', 
                'detalle__color',
                'detalle__produccion__operador'
            ).get(codigo_unico__iexact=codigo)
        except Paca.DoesNotExist:
            error_mensaje = f"No se encontró ninguna paca registrada con el código: '{codigo}'"

    return render(
        request,
        "produccion/buscar_codigo.html", 
        {
            "paca": paca,
            "codigo": codigo,
            "error_mensaje": error_mensaje,
        }
    )