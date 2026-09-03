from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.produccion.models import Operador, Turno, Color, Produccion, DetalleProduccion, Producto, Paca

def login_operador(request):
    """Permite al operador iniciar sesión ingresando su cédula o código de acceso"""
    if request.method == 'POST':
        ingreso = request.POST.get('cedula', '').strip()
        
        try:
            operador = Operador.objects.get(cedula=ingreso, activo=True)
        except Operador.DoesNotExist:
            try:
                operadores_activos = Operador.objects.filter(activo=True)
                operador = None
                for op in operadores_activos:
                    partes = op.nombre_completo.split()
                    if len(partes) >= 2:
                        iniciales = f"{partes[0][0]}{partes[1][0]}".upper()
                    elif len(partes) == 1:
                        iniciales = f"{partes[0][0]}X".upper()
                    else:
                        iniciales = ""
                        
                    ultimos_cedula = op.cedula[-4:] if len(op.cedula) >= 4 else op.cedula
                    codigo_generado = f"{iniciales}{ultimos_cedula}".upper()
                    
                    if ingreso.upper() == codigo_generado or ingreso.upper() == op.cedula.upper():
                        operador = op
                        break
                
                if not operador:
                    raise Operador.DoesNotExist
            except Operador.DoesNotExist:
                messages.error(request, "Credencial no encontrada o el operador se encuentra inactivo.")
                return redirect('operadores:login_operador')
            
        request.session['operador_id'] = operador.id
        request.session['operador_nombre'] = operador.nombre_completo
        
        # Limpiamos turno y color al iniciar sesión para forzar la selección inicial
        request.session.pop('turno_id', None)
        request.session.pop('color_id', None)
        
        return redirect('operadores:terminal_operador')
            
    return render(request, 'login_operadores/login_operador.html')

def terminal_operador(request):
    """Vista principal de la terminal táctil del operador con generación de códigos"""
    operador_id = request.session.get('operador_id')
    if not operador_id:
        return redirect('operadores:login_operador')
        
    operador = get_object_or_404(Operador, id=operador_id)
    
    turnos = Turno.objects.all()
    colores = Color.objects.all()
    productos = Producto.objects.all()

    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        # Si envían la configuración inicial o cambio de turno/color
        if accion == 'configurar':
            turno_id = request.POST.get('turno_id')
            color_id = request.POST.get('color_id')
            if turno_id and color_id:
                request.session['turno_id'] = turno_id
                request.session['color_id'] = color_id
                messages.success(request, "¡Turno y Color configurados correctamente!")
            return redirect('operadores:terminal_operador')
            
        # Si están registrando una paca mediante un toque en el modelo
        producto_id = request.POST.get('producto_id')
        turno_id = request.session.get('turno_id')
        color_id = request.session.get('color_id')
        
        if not turno_id or not color_id:
            messages.error(request, "Por favor seleccione el Turno y Color de trabajo.")
            return redirect('operadores:terminal_operador')
            
        if producto_id:
            producto = get_object_or_404(Producto, id=producto_id)
            turno = get_object_or_404(Turno, id=turno_id)
            color = get_object_or_404(Color, id=color_id)
            
            hoy = timezone.now().date()
            produccion, created = Produccion.objects.get_or_create(
                fecha=hoy,
                operador=operador,
                turno=turno,
                defaults={'observacion': 'Registrado desde Terminal Táctil'}
            )
            
            detalle, created_det = DetalleProduccion.objects.get_or_create(
                produccion=produccion,
                producto=producto,
                color=color,
                defaults={'cantidad_pacas': 0}
            )
            
            # Incrementamos la cantidad en 1 paca por cada toque táctil
            detalle.cantidad_pacas += 1
            detalle.save()
            
            # --- GENERACIÓN AUTOMÁTICA DEL CÓDIGO ÚNICO (LÓGICA CORREGIDA) ---
            iniciales_op = produccion.operador.obtener_iniciales()
            fecha_formateada = produccion.fecha.strftime('%d%m%y')
            codigo_prod_col = f"{producto.codigo.strip().upper()}{color.codigo.strip().upper()}"
            
            # Buscamos la última paca registrada en la base de datos para este producto y color (excluyendo la que estamos creando en este mismo instante)
            ultima_paca = Paca.objects.filter(
                detalle__producto=producto,
                detalle__color=color
            ).exclude(detalle=detalle, id__in=[p.id for p in detalle.paca_set.all()] if hasattr(detalle, 'paca_set') else []).order_by('-id').first()

            # Si ya existían pacas previas y el último lote no se ha llenado (es menor a 50)
            if ultima_paca and ultima_paca.numero_paca < 50:
                lote_heredado = ultima_paca.lote
                paca_anterior_en_lote = ultima_paca.numero_paca
            else:
                lote_heredado = 0
                paca_anterior_en_lote = 0

            # Contamos cuántas pacas lleva este detalle en curso
            total_actual_pacas = Paca.objects.filter(detalle=detalle).count()
            
            if paca_anterior_en_lote > 0 and paca_anterior_en_lote < 50:
                # Continuamos llenando el lote incompleto anterior
                paca_en_lote = paca_anterior_en_lote + total_actual_pacas
                num_lote = lote_heredado
            else:
                # Arrancamos lotes nuevos de 50 en 50
                num_lote = ((total_actual_pacas - 1) // 50) + 1
                paca_en_lote = ((total_actual_pacas - 1) % 50) + 1

            lote_formateado = f"L{num_lote:02d}"
            paca_formateada = f"{paca_en_lote:03d}"
            nuevo_codigo_unico = f"{iniciales_op}{fecha_formateada}{codigo_prod_col}{paca_formateada}{lote_formateado}"

            # Creamos la paca individual en la base de datos
            Paca.objects.create(
                detalle=detalle,
                numero_paca=paca_en_lote,
                lote=num_lote,
                codigo_unico=nuevo_codigo_unico
            )
            # -----------------------------------------------------------------
            
            messages.success(request, f"¡Paca de {producto.nombre} ({color.nombre}) registrada con éxito!")
            
        return redirect('operadores:terminal_operador')

    turno_actual_id = request.session.get('turno_id')
    color_actual_id = request.session.get('color_id')
    
    turno_actual = Turno.objects.filter(id=turno_actual_id).first() if turno_actual_id else None
    color_actual = Color.objects.filter(id=color_actual_id).first() if color_actual_id else None

    context = {
        'operador_nombre': operador.nombre_completo,
        'turnos': turnos,
        'colores': colores,
        'productos': productos,
        'turno_actual': turno_actual,
        'color_actual': color_actual,
        'necesita_config': not (turno_actual and color_actual),
        'fecha_hoy': timezone.now().date(),
    }
    return render(request, 'login_operadores/terminal_operador.html', context)

def logout_operador(request):
    request.session.flush()
    return redirect('operadores:login_operador')