from django.urls import path
from . import views

app_name = 'operadores'

urlpatterns = [
    path('login/', views.login_operador, name='login_operador'),
    path('terminal/', views.terminal_operador, name='terminal_operador'),
    path('logout/', views.logout_operador, name='logout_operador'),
]