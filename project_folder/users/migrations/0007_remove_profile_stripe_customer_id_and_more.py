# Generated by Django 5.1.6 on 2025-05-26 02:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_migrate_stripe_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='stripe_customer_id',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='stripe_last_intent_id',
        ),
    ]
