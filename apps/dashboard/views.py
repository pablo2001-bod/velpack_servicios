from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.despachos.models import Despacho
from apps.inventario.services import calcular_stock_inventario


@login_required
def index_view(request):
    context = calcular_stock_inventario()
    context["despachos_pendientes"] = (
        Despacho.objects.filter(estado__iexact="PENDIENTE")
        .select_related("cliente")
        .order_by("fecha", "id")
    )
    return render(request, "dashboard/index.html", context)
