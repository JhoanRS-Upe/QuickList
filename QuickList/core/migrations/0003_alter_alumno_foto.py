# Generated by Django 5.1.3 on 2024-11-27 11:47

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alumno_foto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alumno',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to=core.models.PathAndRename('alumnos_fotos/')),
        ),
    ]
