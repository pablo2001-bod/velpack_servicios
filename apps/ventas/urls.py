from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Lista de ventas (Solo lectura)
    path('', views.lista_ventas, name='lista_ventas'),
    
    # Registro de nueva venta (Con confirmación antes de guardar)
    path('crear/', views.crear_venta, name='crear_venta'),
]