from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.inventario.services import calcular_stock_inventario
from apps.produccion.services import obtener_stock_materia_prima


@login_required
def dashboard_inventario(request):
    context = calcular_stock_inventario()
    context["materia_prima_por_tipo"] = obtener_stock_materia_prima()
    return render(request, "inventario/dashboard.html", context)
