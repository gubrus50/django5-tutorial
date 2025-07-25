# Generated by Django 5.1.6 on 2025-07-13 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_account_deletion_task_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='deletion_task_id',
        ),
        migrations.AddField(
            model_name='account',
            name='deletion_phase',
            field=models.CharField(choices=[('pending', 'Pending Deletion'), ('stripe_started', 'Stripe Deletion Started'), ('stripe_completed', 'Stripe Deletion Completed'), ('user_deletable', 'User Ready for Deletion'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
    ]
