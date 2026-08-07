from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import user_passes_test
from apps.produccion.models import Operador

# ==========================================================
# REGISTRO Y LISTADO PRINCIPAL
# ==========================================================

# Decorador para restringir que solo los superusuarios (administradores) entren a esta vista
@user_passes_test(lambda u: u.is_superuser)
def registrar_usuario(request):
    if request.method == 'POST':
        rol = request.POST.get('rol')

        if rol == 'operador':
            nombre = request.POST.get('first_name')
            apellido = request.POST.get('last_name')
            cedula = request.POST.get('cedula')
            nombre_completo = f"{nombre} {apellido}".strip()

            if Operador.objects.filter(cedula=cedula).exists():
                messages.error(request, "Ya existe un operador registrado con esa cédula.")
                return redirect('registrar_usuario')

            Operador.objects.create(
                nombre_completo=nombre_completo,
                cedula=cedula,
                activo=True
            )
            messages.success(request, f"Operador '{nombre_completo}' registrado con éxito para producción.")
            
            # Redirección directa sin namespace 'accounts:'
            return redirect('lista_usuarios')

        else:
            # Flujo para cuentas con acceso de login (Admin / Normal)
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')

            if User.objects.filter(username=username).exists():
                messages.error(request, "El nombre de usuario ya existe.")
                return redirect('registrar_usuario')

            User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=make_password(password),
                is_superuser=(rol == 'superusuario'),
                is_staff=(rol == 'superusuario') # Permiso de staff si es superusuario
            )
            messages.success(request, f"Usuario de acceso '{username}' registrado con éxito.")
            
            # Redirección directa sin namespace 'accounts:'
            return redirect('lista_usuarios')

    return render(request, 'accounts/registrar_usuario.html')


# Vista de la lista de usuarios
@user_passes_test(lambda u: u.is_superuser)
def lista_usuarios(request):
    usuarios_sistema = User.objects.all().order_by('-date_joined')
    operadores_produccion = Operador.objects.all().order_by('nombre_completo')
    
    return render(
        request, 
        'accounts/lista_usuarios.html', 
        {
            'usuarios_sistema': usuarios_sistema,
            'operadores_produccion': operadores_produccion
        }
    )


# ==========================================================
# ACCIONES PARA OPERADORES DE PRODUCCIÓN
# ==========================================================

@user_passes_test(lambda u: u.is_superuser)
def editar_operador(request, pk):
    operador = get_object_or_404(Operador, pk=pk)
    
    if request.method == 'POST':
        nombre = request.POST.get('first_name')
        apellido = request.POST.get('last_name')
        cedula = request.POST.get('cedula')
        activo = request.POST.get('activo') == 'on' # Captura si el checkbox está marcado

        nombre_completo = f"{nombre} {apellido}".strip()

        # Evitar duplicados de cédula con otros operadores existentes
        if Operador.objects.filter(cedula=cedula).exclude(pk=pk).exists():
            messages.error(request, "Ya existe otro operador registrado con esa cédula.")
            return redirect('editar_operador', pk=pk)

        operador.nombre_completo = nombre_completo
        operador.cedula = cedula
        operador.activo = activo
        operador.save()

        messages.success(request, f"Operador '{nombre_completo}' actualizado correctamente.")
        return redirect('lista_usuarios')

    # Separamos el nombre completo para rellenar los inputs "Nombres" y "Apellidos"
    partes = operador.nombre_completo.split(' ', 1)
    nombre = partes[0] if len(partes) > 0 else ""
    apellido = partes[1] if len(partes) > 1 else ""

    return render(request, 'accounts/editar_operador.html', {
        'operador': operador,
        'nombre': nombre,
        'apellido': apellido
    })


@user_passes_test(lambda u: u.is_superuser)
def eliminar_operador(request, pk):
    operador = get_object_or_404(Operador, pk=pk)
    nombre_completo = operador.nombre_completo
    operador.delete()
    messages.success(request, f"Operador '{nombre_completo}' eliminado con éxito.")
    return redirect('lista_usuarios')


# ==========================================================
# ACCIONES PARA USUARIOS DEL SISTEMA
# ==========================================================

@user_passes_test(lambda u: u.is_superuser)
def editar_usuario(request, pk):
    usuario_edit = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        rol = request.POST.get('rol')
        password = request.POST.get('password') # Contraseña es opcional al editar
        activo = request.POST.get('activo') == 'on'

        # Evitar conflicto de usernames con otros
        if User.objects.filter(username=username).exclude(pk=pk).exists():
            messages.error(request, "El nombre de usuario ya está registrado por otra cuenta.")
            return redirect('editar_usuario', pk=pk)

        usuario_edit.username = username
        usuario_edit.email = email
        usuario_edit.first_name = first_name
        usuario_edit.last_name = last_name
        usuario_edit.is_superuser = (rol == 'superusuario')
        usuario_edit.is_staff = (rol == 'superusuario')
        usuario_edit.is_active = activo

        if password: # Solo actualiza la contraseña si el administrador digitó una nueva
            usuario_edit.password = make_password(password)

        usuario_edit.save()
        messages.success(request, f"Cuenta de usuario '{username}' actualizada correctamente.")
        return redirect('lista_usuarios')

    return render(request, 'accounts/editar_usuario.html', {'usuario_edit': usuario_edit})


@user_passes_test(lambda u: u.is_superuser)
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    
    # Doble validación de seguridad para que el administrador no se borre a sí mismo
    if usuario == request.user:
        messages.error(request, "¡Acción denegada! No puedes eliminar tu propia cuenta en sesión.")
        return redirect('lista_usuarios')

    username = usuario.username
    usuario.delete()
    messages.success(request, f"Usuario de acceso '{username}' eliminado correctamente.")
    return redirect('lista_usuarios')