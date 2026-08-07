from django.urls import path
from . import views

app_name = 'proveedores'

urlpatterns = [
    # Rutas para Proveedores
    path('', views.lista_proveedores, name='lista_proveedores'),
    path('crear/', views.crear_proveedor, name='crear_proveedor'),
    path('editar/<int:pk>/', views.editar_proveedor, name='editar_proveedor'),
    path('eliminar/<int:pk>/', views.eliminar_proveedor, name='eliminar_proveedor'),

    # Rutas para el Ingreso de Materia Prima
    path('ingresos/', views.lista_ingresos, name='lista_ingresos'),
    path('ingresos/nuevo/', views.crear_ingreso, name='crear_ingreso'),
]