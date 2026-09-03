from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard_analiticas, name='panel'),
]