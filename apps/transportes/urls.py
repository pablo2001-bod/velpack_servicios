from django.urls import path
from . import views

# Asegúrate de definir el nombre de la app si lo estás usando así
app_name = 'transportes'

urlpatterns = [
    path('', views.lista_transportes, name='lista_transportes'),
    path('crear/', views.crear_transporte, name='crear_transporte'),
    path('editar/<int:pk>/', views.editar_transporte, name='editar_transporte'),
    path('eliminar/<int:pk>/', views.eliminar_transporte, name='eliminar_transporte'),
]