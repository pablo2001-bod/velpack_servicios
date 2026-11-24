from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("despachos", "0005_alter_detalledespacho_color_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="despacho",
            name="ruc_emisor",
            field=models.CharField(default="0591746284001", max_length=20, verbose_name="R.U.C. emisor"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="direccion_emisor",
            field=models.CharField(
                default="Av. Eloy Alfaro y Los Molinos, Latacunga",
                max_length=255,
                verbose_name="Dirección del emisor",
            ),
        ),
        migrations.AddField(
            model_name="despacho",
            name="ciudad_emisor",
            field=models.CharField(
                default="Latacunga - Ecuador", max_length=100, verbose_name="Ciudad del emisor"
            ),
        ),
        migrations.AddField(
            model_name="despacho",
            name="contribuyente",
            field=models.CharField(default="Especial 011", max_length=100, verbose_name="Contribuyente"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="agente_retencion",
            field=models.CharField(
                default="Resolución No. 1", max_length=100, verbose_name="Agente de retención"
            ),
        ),
        migrations.AddField(
            model_name="despacho",
            name="ambiente",
            field=models.CharField(default="PRODUCCIÓN", max_length=30, verbose_name="Ambiente"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="emision",
            field=models.CharField(default="NORMAL", max_length=30, verbose_name="Emisión"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="punto_partida",
            field=models.CharField(default="LATACUNGA", max_length=100, verbose_name="Punto de partida"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="estado_transporte",
            field=models.CharField(default="En tránsito", max_length=50, verbose_name="Estado impreso"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="motivo",
            field=models.CharField(default="VENTA", max_length=100, verbose_name="Motivo"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="ruta",
            field=models.CharField(default="LATACUNGA - SALCEDO", max_length=150, verbose_name="Ruta"),
        ),
        migrations.AddField(
            model_name="despacho",
            name="correo_empresa",
            field=models.EmailField(
                blank=True,
                default="velpack.2021@gmail.com",
                max_length=254,
                verbose_name="Correo de la empresa",
            ),
        ),
        migrations.AddField(
            model_name="despacho",
            name="telefono_empresa",
            field=models.CharField(default="03-2800-000", max_length=30, verbose_name="Teléfono de la empresa"),
        ),
    ]
