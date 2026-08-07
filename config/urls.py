from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect

# Vista rápida para permitir logout por GET/POST
def logout_view(request):
    logout(request)
    return redirect('login')

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # --- RUTAS DE AUTENTICACIÓN ---
    # Apuntamos a 'accounts/login.html' como está en tu estructura
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    
    # --- APPS DEL SISTEMA ---
    path("", include("apps.dashboard.urls")),
    path("produccion/", include("apps.produccion.urls")),
    path('accounts/', include('apps.accounts.urls')),
    path('clientes/', include(('apps.clientes.urls', 'clientes'))), 
    path('proveedores/', include(('apps.proveedores.urls', 'proveedores'))),
    path('transportes/', include(('apps.transportes.urls', 'transportes'))),
    path('ventas/', include(('apps.ventas.urls', 'ventas'))),
    path('despachos/', include(('apps.despachos.urls', 'despachos'))),
    path('reportes/', include(('apps.reportes.urls', 'reportes'))),
    path('inventario/', include(('apps.inventario.urls', 'inventario'), namespace='inventario')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )