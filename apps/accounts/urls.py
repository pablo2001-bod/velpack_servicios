from django.urls import path
from . import views

# NO pongas app_name = 'accounts' si te da problemas. Déjalo directo:

urlpatterns = [
    # Definimos la ruta para registrar que apunta a tu plantilla de registrar_usuario.html
   path('lista/', views.lista_usuarios, name='lista_usuarios'), 
    path('registrar/', views.registrar_usuario, name='registrar_usuario'),
    path('operador/editar/<int:pk>/', views.editar_operador, name='editar_operador'),
    path('operador/eliminar/<int:pk>/', views.eliminar_operador, name='eliminar_operador'),

    # Rutas para Usuarios del Sistema
    path('usuario/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('usuario/eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),

    path('turnos/nuevo/', views.crear_turno, name='crear_turno'),
    path('turnos/<int:pk>/editar/', views.editar_turno, name='editar_turno'),
    path('turnos/<int:pk>/eliminar/', views.eliminar_turno, name='eliminar_turno'),
]