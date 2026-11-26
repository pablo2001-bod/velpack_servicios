from django.urls import path
from . import views

app_name = "produccion"

urlpatterns = [
    path('lista/', views.lista_produccion, name='lista'),
    path("registrar/", views.gestionar_cronograma, name="registrar"),
    path("modelos/nuevo/", views.crear_modelo, name="modelo_crear"),
    path("modelos/<int:pk>/editar/", views.editar_modelo, name="modelo_editar"),
    path("modelos/<int:pk>/eliminar/", views.eliminar_modelo, name="modelo_eliminar"),
    path("colores/nuevo/", views.crear_color, name="color_crear"),
    path("colores/<int:pk>/editar/", views.editar_color, name="color_editar"),
    path("colores/<int:pk>/eliminar/", views.eliminar_color, name="color_eliminar"),
    path("configuracion/", views.configurar_produccion, name="configuracion"),
    path("parametros/", views.lista_parametros, name="parametros"),
    path("parametros/nuevo/", views.crear_parametro, name="parametro_crear"),
    path("parametros/<int:pk>/editar/", views.editar_parametro, name="parametro_editar"),
    path("parametros/<int:pk>/eliminar/", views.eliminar_parametro, name="parametro_eliminar"),
    path("agregar-produccion/", views.registrar_produccion_admin, name="agregar_produccion"),
    path("pdf/<int:id>/", views.descargar_pdf, name="descargar_pdf"),
    path("pdf/produccion/<int:id>/", views.pdf_produccion, name="pdf_produccion"),
    path("detalle/<int:id>/", views.detalle_produccion, name="detalle_produccion"),
    path("buscar/", views.buscar_codigo, name="buscar_codigo"),
    path("paca/<str:codigo>/", views.ficha_paca, name="ficha_paca"),
    path("etiquetas/<int:id>/", views.imprimir_etiquetas, name="etiquetas"),
]