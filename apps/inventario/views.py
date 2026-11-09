from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from apps.inventario.services import calcular_stock_inventario
from apps.proveedores.models import IngresoMateriaPrima


@login_required
def dashboard_inventario(request):
    materia_prima_por_tipo = (
        IngresoMateriaPrima.objects.values("tipo_material")
        .annotate(total_peso=Sum("peso_neto"))
        .order_by("-total_peso")
    )

    context = calcular_stock_inventario()
    context["materia_prima_por_tipo"] = materia_prima_por_tipo
    return render(request, "inventario/dashboard.html", context)
