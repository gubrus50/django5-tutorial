from django.contrib import admin
from .models import Profile



class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = (
        'stripe_customer_id',
        'stripe_last_intent_id'
    )
    list_display = [field.name for field in Profile._meta.fields]


# Register your models here.
admin.site.register(Profile, ProfileAdmin)