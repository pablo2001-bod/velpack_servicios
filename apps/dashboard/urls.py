# apps/dashboard/urls.py
from django.urls import path
from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    # Al dejarlo vacío "", se convierte en la página de inicio predeterminada de la app
    path("", views.index_view, name="inicio"), 
]