# Generated by Django 5.1.6 on 2025-03-14 03:48

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='users_online',
            field=models.ManyToManyField(blank=True, related_name='online_in_rooms', to=settings.AUTH_USER_MODEL),
        ),
    ]
