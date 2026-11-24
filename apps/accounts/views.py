from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from apps.produccion.models import Operador, Turno

from .forms import TurnoForm
from .models import AvisoInterno, PerfilUsuario


def _solo_superusuario(view):
    return user_passes_test(lambda u: u.is_superuser)(view)


def _clave_valida(request, password, username=""):
    usuario_temporal = User(username=username)
    try:
        validate_password(password, usuario_temporal)
    except ValidationError as errores:
        for error in errores.messages:
            messages.error(request, error)
        return False
    return True


# ==========================================================
# REGISTRO Y LISTADO PRINCIPAL
# ==========================================================


@_solo_superusuario
def registrar_usuario(request):
    if request.method == "POST":
        rol = request.POST.get("rol")

        if rol == "operador":
            nombre = request.POST.get("first_name", "").strip()
            apellido = request.POST.get("last_name", "").strip()
            cedula = request.POST.get("cedula", "").strip()
            nombre_completo = f"{nombre} {apellido}".strip()

            if not nombre_completo or not cedula:
                messages.error(request, "El nombre y la cédula del operador son obligatorios.")
                return redirect("registrar_usuario")

            if Operador.objects.filter(cedula=cedula).exists():
                messages.error(request, "Ya existe un operador registrado con esa cédula.")
                return redirect("registrar_usuario")

            Operador.objects.create(
                nombre_completo=nombre_completo,
                cedula=cedula,
                activo=True,
            )
            messages.success(
                request,
                f"Operador '{nombre_completo}' registrado con éxito para producción.",
            )
            return redirect("lista_usuarios")

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if not username or not password:
            messages.error(request, "El usuario y la contraseña son obligatorios.")
            return redirect("registrar_usuario")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
            return redirect("registrar_usuario")

        if not _clave_valida(request, password, username):
            return redirect("registrar_usuario")

        es_superusuario = rol == "superusuario"
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_superuser=es_superusuario,
                is_staff=es_superusuario,
            )
            PerfilUsuario.obtener_o_crear_para(usuario)

        messages.success(
            request,
            f"Usuario de acceso '{username}' registrado con éxito.",
        )
        return redirect("lista_usuarios")

    return render(request, "accounts/registrar_usuario.html")


@_solo_superusuario
def lista_usuarios(request):
    usuarios_sistema = User.objects.all().order_by("-date_joined")
    operadores_produccion = Operador.objects.all().order_by("nombre_completo")

    return render(
        request,
        "accounts/lista_usuarios.html",
        {
            "usuarios_sistema": usuarios_sistema,
            "operadores_produccion": operadores_produccion,
            "turnos": Turno.objects.all().order_by("hora_inicio", "nombre"),
        },
    )


# ==========================================================
# ACCIONES PARA OPERADORES DE PRODUCCIÓN
# ==========================================================


@_solo_superusuario
def editar_operador(request, pk):
    operador = get_object_or_404(Operador, pk=pk)

    if request.method == "POST":
        nombre = request.POST.get("first_name", "").strip()
        apellido = request.POST.get("last_name", "").strip()
        cedula = request.POST.get("cedula", "").strip()
        activo = request.POST.get("activo") == "on"

        nombre_completo = f"{nombre} {apellido}".strip()
        if not nombre_completo or not cedula:
            messages.error(request, "El nombre y la cédula del operador son obligatorios.")
            return redirect("editar_operador", pk=pk)

        if Operador.objects.filter(cedula=cedula).exclude(pk=pk).exists():
            messages.error(request, "Ya existe otro operador registrado con esa cédula.")
            return redirect("editar_operador", pk=pk)

        operador.nombre_completo = nombre_completo
        operador.cedula = cedula
        operador.activo = activo
        operador.save(update_fields=["nombre_completo", "cedula", "activo"])

        messages.success(
            request, f"Operador '{nombre_completo}' actualizado correctamente."
        )
        return redirect("lista_usuarios")

    nombre, _, apellido = operador.nombre_completo.partition(" ")

    return render(
        request,
        "accounts/editar_operador.html",
        {
            "operador": operador,
            "nombre": nombre,
            "apellido": apellido,
        },
    )


@_solo_superusuario
def eliminar_operador(request, pk):
    operador = get_object_or_404(Operador, pk=pk)
    nombre_completo = operador.nombre_completo

    try:
        operador.delete()
    except ProtectedError:
        messages.error(
            request,
            f"No se puede eliminar a '{nombre_completo}' porque tiene producción registrada.",
        )
    else:
        messages.success(
            request, f"Operador '{nombre_completo}' eliminado con éxito."
        )
    return redirect("lista_usuarios")


# ==========================================================
# ACCIONES PARA USUARIOS DEL SISTEMA
# ==========================================================


@_solo_superusuario
def editar_usuario(request, pk):
    usuario_edit = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        rol = request.POST.get("rol")
        password = request.POST.get("password", "")
        activo = request.POST.get("activo") == "on"

        if not username:
            messages.error(request, "El nombre de usuario es obligatorio.")
            return redirect("editar_usuario", pk=pk)

        if User.objects.filter(username=username).exclude(pk=pk).exists():
            messages.error(
                request,
                "El nombre de usuario ya está registrado por otra cuenta.",
            )
            return redirect("editar_usuario", pk=pk)

        es_superusuario = rol == "superusuario"
        usuario_edit.username = username
        usuario_edit.email = email
        usuario_edit.first_name = first_name
        usuario_edit.last_name = last_name
        usuario_edit.is_superuser = es_superusuario
        usuario_edit.is_staff = es_superusuario
        usuario_edit.is_active = activo

        if password:
            if not _clave_valida(request, password, username):
                return redirect("editar_usuario", pk=pk)
            usuario_edit.set_password(password)

        usuario_edit.save()
        PerfilUsuario.obtener_o_crear_para(usuario_edit)

        messages.success(
            request,
            f"Cuenta de usuario '{username}' actualizada correctamente.",
        )
        return redirect("lista_usuarios")

    return render(
        request,
        "accounts/editar_usuario.html",
        {"usuario_edit": usuario_edit},
    )


@_solo_superusuario
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    if usuario == request.user:
        messages.error(
            request,
            "¡Acción denegada! No puedes eliminar tu propia cuenta en sesión.",
        )
        return redirect("lista_usuarios")

    username = usuario.username
    usuario.delete()
    messages.success(
        request, f"Usuario de acceso '{username}' eliminado correctamente."
    )
    return redirect("lista_usuarios")


# ==========================================================
# TURNOS OPERATIVOS (SOLO ADMINISTRADOR)
# ==========================================================


@_solo_superusuario
def crear_turno(request):
    if request.method == "POST":
        form = TurnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Turno operativo creado correctamente.")
            return redirect("lista_usuarios")
    else:
        form = TurnoForm()
    return render(
        request,
        "accounts/turno_form.html",
        {"form": form, "titulo": "Nuevo turno operativo"},
    )


@_solo_superusuario
def editar_turno(request, pk):
    turno = get_object_or_404(Turno, pk=pk)
    if request.method == "POST":
        form = TurnoForm(request.POST, instance=turno)
        if form.is_valid():
            form.save()
            messages.success(request, "Turno operativo actualizado correctamente.")
            return redirect("lista_usuarios")
    else:
        form = TurnoForm(instance=turno)
    return render(
        request,
        "accounts/turno_form.html",
        {"form": form, "titulo": "Editar turno operativo"},
    )


@_solo_superusuario
def eliminar_turno(request, pk):
    turno = get_object_or_404(Turno, pk=pk)
    try:
        turno.delete()
    except ProtectedError:
        turno.activo = False
        turno.save(update_fields=["activo"])
        messages.warning(
            request,
            "El turno tiene producción registrada: se desactivó en lugar de eliminarse.",
        )
    else:
        messages.success(request, "Turno eliminado correctamente.")
    return redirect("lista_usuarios")


# ==========================================================
# AVISOS INTERNOS
# ==========================================================


@_solo_superusuario
def lista_avisos(request):
    avisos = AvisoInterno.objects.select_related("usuario", "operador").all()
    return render(request, "accounts/avisos.html", {"avisos": avisos})


@_solo_superusuario
def marcar_aviso_leido(request, pk):
    if request.method == "POST":
        aviso = get_object_or_404(AvisoInterno, pk=pk)
        aviso.leido = True
        aviso.save(update_fields=["leido"])
    return redirect("lista_avisos")


@_solo_superusuario
def marcar_todos_leidos(request):
    if request.method == "POST":
        AvisoInterno.objects.filter(leido=False).update(leido=True)
        messages.success(request, "Avisos marcados como leídos.")
    return redirect("lista_avisos")
