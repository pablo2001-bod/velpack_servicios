from .models import AvisoInterno


def avisos(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_superuser:
        return {"avisos_pendientes": 0, "avisos_recientes": []}

    avisos_qs = AvisoInterno.objects.all()
    return {
        "avisos_pendientes": avisos_qs.filter(leido=False).count(),
        "avisos_recientes": list(avisos_qs[:5]),
    }
