from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.panel_reportes, name='panel'),
    
    # Clientes
    path('clientes/', views.reporte_clientes, name='clientes'),
    path('clientes/excel/', views.exportar_clientes_excel, name='exportar_clientes_excel'),

    # Proveedores
    path('proveedores/', views.reporte_proveedores, name='proveedores'),
    path('proveedores/excel/', views.exportar_proveedores_excel, name='exportar_proveedores_excel'),

    # Transportes / Choferes
    path('transportes/', views.reporte_transportes, name='transportes'),
    path('transportes/excel/', views.exportar_transportes_excel, name='exportar_transportes_excel'),

    # Materia Prima
    path('materia-prima/', views.reporte_materia_prima, name='materia_prima'),
    path('materia-prima/excel/', views.exportar_materia_prima_excel, name='exportar_materia_prima_excel'),
    
    # Producción
    path('produccion/', views.reporte_produccion, name='reporte_produccion'),
    path('produccion/excel/', views.exportar_produccion_excel, name='exportar_produccion_excel'),

    # Ventas
    path('ventas/', views.reporte_ventas, name='ventas'),
    path('ventas/excel/', views.exportar_ventas_excel, name='exportar_ventas_excel'),

    # Despachos
    path('despachos/', views.reporte_despachos, name='despachos'),
    path('despachos/excel/', views.exportar_despachos_excel, name='exportar_despachos_excel'),

    path('usuarios/', views.reporte_usuarios, name='reporte_usuarios'),
    path('usuarios/excel/', views.exportar_usuarios_excel, name='exportar_usuarios_excel'),
]