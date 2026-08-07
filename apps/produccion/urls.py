from django.urls import path
from . import views

app_name = "produccion"

urlpatterns = [
    path('lista/', views.lista_produccion, name='lista'), 
    path("registrar/", views.registrar_produccion, name="registrar"),
    path("detalle/<int:id>/", views.detalle_produccion, name="detalle_produccion"),
    path("buscar/", views.buscar_codigo, name="buscar_codigo"),
]
