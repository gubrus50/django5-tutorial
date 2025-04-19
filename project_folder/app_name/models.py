from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# Create your models here.
class ModelName(models.Model):

    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(
        verbose_name=_('My Title'),
        max_length=100,
        blank=False,
    )

    COUNTRIES = [
        ('GB', 'Great Britain'),
        ('PL', 'Polska'),
        ('DE', 'Deutschland'),
    ]

    country = models.CharField(
        verbose_name=_('Select a country'),
        max_length=2,
        default=COUNTRIES[1][1],
        choices=COUNTRIES,
        blank=False,
    )
