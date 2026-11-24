from django.db import migrations, models


def borrar_avisos_pedido_web(apps, schema_editor):
    AvisoInterno = apps.get_model("accounts", "AvisoInterno")
    AvisoInterno.objects.filter(tipo="pedido_web").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_avisointerno_tipo"),
    ]

    operations = [
        migrations.RunPython(borrar_avisos_pedido_web, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="avisointerno",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("ingreso_usuario", "Ingreso de usuario"),
                    ("ingreso_operador", "Ingreso de operador"),
                ],
                max_length=30,
            ),
        ),
    ]
