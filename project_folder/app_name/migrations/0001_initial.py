# Generated by Django 5.1.6 on 2025-02-15 13:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelName',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100, verbose_name='My Title')),
                ('country', models.CharField(choices=[('GB', 'Great Britain'), ('PL', 'Polska'), ('DE', 'Deutschland')], default='Polska', max_length=2, verbose_name='Select a country')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
