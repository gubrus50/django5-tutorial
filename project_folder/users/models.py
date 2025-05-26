from django.db import models
from django.contrib.auth.models import User
from django_resized import ResizedImageField
from django.conf import settings

from .utils import (
    remove_profile_pic,
    recycle_profile_pic,
    get_or_create_stripe_customer,
)




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    image = ResizedImageField(
        size=[300, 300],
        crop=['middle', 'center'],
        quality=75,
        force_format='JPEG',
        upload_to='profile_pics',
        default='default_profile.jpg'
    )
    
    def save(self, *args, **kwargs):
        try:
            this = Profile.objects.get(user=self.user)

            # Only move the old image if there is an existing image and it's different from the new image
            if this.image and this.image.name != self.image.name:
                #recycle_profile_pic(this.image.name)
                remove_profile_pic(this.image.name)

        except Profile.DoesNotExist:
            # This is a new profile, so no need to move any image.
            pass


        super().save(*args, **kwargs)
        



class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # State
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    suspension_end = models.DateTimeField(blank=True, null=True)

    # Security
    has_verified_email = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=16, blank=True, null=True)
    mfa_enabled = models.BooleanField(default=False)
    #backup_codes = ""

    # Payment
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, unique=True, editable=False)
    stripe_last_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True, editable=False)


    def save(self, *args, **kwargs):
        try:
            account_instance = Account.objects.get(user=self.user)

            # Create Stripe customer for new Account. (Stripe is used for making payments)
            if not hasattr(account_instance, 'stripe_customer_id'):
                self.stripe_customer_id = get_or_create_stripe_customer(self.user)

        except Account.DoesNotExist:
            pass


        super().save(*args, **kwargs)