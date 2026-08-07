from django.urls import path
from . import views

app_name = 'despachos'

urlpatterns = [
    path('lista/', views.lista_despacho, name='lista'),
    path('crear/', views.crear_despacho, name='crear'),
    path('entregar/<int:id>/', views.marcar_entregado, name='entregar'),
    path('editar/<int:id>/', views.editar_despacho, name='editar'),
    path('ver/<int:id>/', views.ver_despacho, name='ver'),
]