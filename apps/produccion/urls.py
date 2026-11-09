from django.urls import path
from . import views

app_name = "produccion"

urlpatterns = [
    path('lista/', views.lista_produccion, name='lista'), 
    path("registrar/", views.gestionar_cronograma, name="registrar"),  # <--- Apunta a gestionar_cronograma
    path("detalle/<int:id>/", views.detalle_produccion, name="detalle_produccion"),
    path("buscar/", views.buscar_codigo, name="buscar_codigo"),
    path("paca/<str:codigo>/", views.ficha_paca, name="ficha_paca"),
    path("etiquetas/<int:id>/", views.imprimir_etiquetas, name="etiquetas"),
]