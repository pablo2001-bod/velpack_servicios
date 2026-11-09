from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from apps.produccion.views import ficha_paca


@require_POST
def logout_view(request):
    """Cierra la sesión solo mediante POST para evitar cierres por enlaces externos."""
    logout(request)
    return redirect('login')


urlpatterns = [
    path("admin/", admin.site.urls),
    
    # --- RUTAS DE AUTENTICACIÓN ---
    # Apuntamos a 'accounts/login.html' como está en tu estructura
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', logout_view, name='logout'),

    # Ruta corta que se graba dentro del QR de las etiquetas.
    path("p/<str:codigo>/", ficha_paca, name="ficha_paca_corta"),
    
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
    path('operador/', include('apps.operadores.urls')),
    path('analytics/', include(('apps.analytics.urls', 'analytics'), namespace='analytics')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )