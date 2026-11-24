from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0002_solicitudpedido"),
    ]

    operations = [
        migrations.DeleteModel(name="SolicitudPedido"),
    ]
