from django.urls import path
from apps.inventario import views

app_name = 'inventario'

urlpatterns = [
    path('', views.dashboard_inventario, name='dashboard'),
]