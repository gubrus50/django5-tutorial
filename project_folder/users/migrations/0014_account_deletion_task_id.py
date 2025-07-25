# Generated by Django 5.1.6 on 2025-07-07 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_account_deletion_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='deletion_task_id',
            field=models.CharField(blank=True, editable=False, help_text='Celery task ID for the deletion process', max_length=255, null=True),
        ),
    ]
