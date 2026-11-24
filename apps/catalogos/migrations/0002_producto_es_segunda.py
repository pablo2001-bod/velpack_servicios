from django.db import migrations, models


def marcar_economica(apps, schema_editor):
    Producto = apps.get_model("catalogos", "Producto")
    productos = Producto.objects.filter(
        models.Q(codigo="S")
        | models.Q(nombre__icontains="segunda")
        | models.Q(nombre__icontains="especial")
    )
    productos.update(nombre="Cubeta Económica", es_segunda=True)


class Migration(migrations.Migration):

    dependencies = [
        ("catalogos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="es_segunda",
            field=models.BooleanField(
                default=False, verbose_name="Línea económica (segunda calidad)"
            ),
        ),
        migrations.RunPython(marcar_economica, migrations.RunPython.noop),
    ]
