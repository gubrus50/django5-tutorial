from django.db import models
from django.contrib.auth.models import User
from django_resized import ResizedImageField
from django.conf import settings

from .utils import get_or_create_stripe_customer

from botocore.exceptions import ClientError
import boto3



s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)


def is_profile_pic(image_key):
    try:
        s3.head_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f"profile_pics/{image_key.split('/')[-1]}"
        )
        return True

    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise e


def remove_profile_pic(image_key):
    if is_profile_pic(image_key):
        # Delete the old image from the original location
        s3.delete_object(
            Key=f"profile_pics/{image_key.split('/')[-1]}",
            Bucket=settings.AWS_STORAGE_BUCKET_NAME
        )


def recycle_profile_pic(image_key):

    if is_profile_pic(image_key):

        profile_pic_key = f"profile_pics/{image_key.split('/')[-1]}"
        recycle_pic_key = f"recycle_pics/{image_key.split('/')[-1]}"

        # Copy the image to the recycle_pics folder
        s3.copy_object(
            Key=recycle_pic_key,
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CopySource={
                'Key': profile_pic_key,
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME
            }
        )
        # Delete the image from the original location
        s3.delete_object(
            Key=profile_pic_key,
            Bucket=settings.AWS_STORAGE_BUCKET_NAME
        )

    else:
        message =  f'Image {image_key} not found in bucket: '
        message += f'{settings.AWS_STORAGE_BUCKET_NAME}'
        message += ', skipping copy and delete.'
        print(message)




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, unique=True, editable=False)
    stripe_last_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True, editable=False)

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

            # Create Stripe customer for new Profile. (Stripe is used for making payments)
            if not hasattr(this, 'stripe_customer_id'):
                self.stripe_customer_id = get_or_create_stripe_customer(self.user)

            # Only move the old image if there is an existing image and it's different from the new image
            if this.image and this.image.name != self.image.name:
                #recycle_profile_pic(this.image.name)
                remove_profile_pic(this.image.name)

        except Profile.DoesNotExist:
            # This is a new profile, so no need to move any image.
            pass


        super().save(*args, **kwargs)
        