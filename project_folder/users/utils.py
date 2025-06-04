from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client

import io, base64, requests, stripe, boto3, pyotp, qrcode
from botocore.exceptions import ClientError

stripe.api_key = settings.STRIPE_SECRET_KEY




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




def is_image_nsfw(image_file: UploadedFile):

    # Push image to DeepAI API to get NSFW score
    response = requests.post(
        url=settings.DEEPAI_NSFW_DETECTOR_URL,
        files={'image': image_file.open('rb')},
        headers={'api-key': settings.DEEPAI_API_KEY}
    )

    result = response.json()

    # Check for status and handle errors
    if result.get('status') != 'success':
        message = "API request failed with status:"
        message += f" {result.get('status')} -"
        message += f" {result.get('error', 'No error message provided')}"
        raise ValueError(message)

    nsfw_score = result.get('output', {}).get('nsfw_score')
    if nsfw_score is None:
        raise ValueError("Unexpected response format: 'output' or 'nsfw_score' key missing.")

    # Adjust the threshold as needed (0.5 = 50%)
    return nsfw_score > 0.5 




def get_or_create_stripe_customer(user):
    """
    Retrieves or creates a Stripe customer ID for the given user.
    
    Args:
        user: Django auth User instance
    
    Returns:
        str: The Stripe customer ID from the user's Account model
    
    Note:
        If no Stripe customer ID exists, this function will:
        1. Create a new Stripe customer account
        2. Save the ID to the user's Account model
        3. Return the newly created ID
    """

    stripe_customer_id = None

    if hasattr(user, 'account'):
        # Retrieve the user's Stripe customer ID from its account
        stripe_customer_id = getattr(user.account, 'stripe_customer_id', None)
    
    if stripe_customer_id is None:
        # Create a new Stripe customer
        customer = stripe.Customer.create(
            name=user.username,
            email=user.email,
            metadata={'user_id': str(user.id)}
        )
        stripe_customer_id = customer.id

        if hasattr(user, 'account'):
            # Update the user's account with the new Stripe customer ID
            user.account.stripe_customer_id = stripe_customer_id
            user.account.save()

    return stripe_customer_id




def get_or_create_mfa_secret_for_user(user_instance):
    """
    Generates a random base32 string and saves it as mfa_secret
    in the, attached to the auth user_instance, account model.

    Returns: 'mfa_secret' from user_instance.account model (on success),
             'False' otherwise.
    """

    if hasattr(user_instance, 'account'):
        if not user_instance.account.mfa_secret:
            user_instance.account.mfa_secret = pyotp.random_base32()
            user_instance.account.save()

    return user_instance.account.mfa_secret or False




def get_users_mfa_secret_as_qrcode_base64(user_instance):
    """
    Generates a Base64-encoded QR code from an MFA secret.

    This function:
    - This function ensure the user has a stored MFA secret.
    - Converts the MFA secret into an OTP provisioning URI.
    - Generates a QR code from the OTP URI.
    - Stores the QR code in an in-memory buffer as a PNG.
    - Encodes the QR code image into a Base64 data URI format.
    
    Args:
        user_instance: A Django User instance.

    Returns:
        str: A Base64-encoded PNG data URI suitable for embedding in HTML.
    """

    mfa_secret = get_or_create_mfa_secret_for_user(user_instance)

    otp_uri = pyotp.totp.TOTP(mfa_secret).provisioning_uri(
        name=user_instance.email,
        issuer_name=settings.OTP_ISSUER_NAME
    )

    # Convert OTP URI to QR Code as PNG
    qr = qrcode.make(otp_uri)     # Convert OTP URI -> QR Code 
    buffer = io.BytesIO()         # Set in-memory buffer to temporarily store the QR Code
    qr.save(buffer, format='PNG') # Convert QR Code -> PNG image & store it in the buffer 
    buffer.seek(0)                # Move buffer's reading position to the beginning

    # Return QR image AS data base64 URI
    qrcode_png_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{qrcode_png_base64}'




def generate_otp_for_user(user_instance, interval=settings.OTP_DEFAULT_INTERVAL):
    """
    Generates a time-based one-time password (OTP) using the user's MFA secret

    This function ensure the user has a stored MFA secret, generates an OTP using TOTP (based on interval)

    Args:
        user_instance: A Django User instance.
        interval: Natural number (in seconds).

    Returns:
        str: The generated OTP
    """

    mfa_secret = get_or_create_mfa_secret_for_user(user_instance)

    totp = pyotp.TOTP(mfa_secret, interval=interval)
    otp = totp.now()

    return otp




def email_otp_to_user(user_instance):
    """
    Generates a time-based one-time password (OTP) using the user's MFA secret and sends it via email.

    This function ensures the user has a stored MFA secret, generates an OTP using TOTP (based on OTP_EMAIL_INTERVAL),
    and delivers it to their registered email address.

    Args:
        user_instance: A Django User instance.

    Returns:
        str: The generated OTP (on success).
        bool: False (on missing otp).
    """

    interval = settings.OTP_EMAIL_INTERVAL

    otp = generate_otp_for_user(user_instance, interval=interval)
    if not otp:
        return False

    # Send OTP via email
    sender_email = settings.EMAIL_HOST_USER
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It expires in {interval} seconds.\n\nPlease do not share this code with anyone!'
    send_mail(subject, message, sender_email, [user_instance.email])

    return otp




def sms_otp_to_user(user_instance):
    """
    Generates a time-based one-time password (OTP) using the user's MFA secret and sends it via SMS.

    This function ensures the user has a stored MFA secret, generates an OTP using TOTP (based on OTP_SMS_INTERVAL),
    and delivers it to their registered in account model - phone number (which should be in E.164 format)

    Args:
        user_instance: A Django User instance linked to an account with MFA enabled.

    Returns:
        str: The generated OTP (on success).
        bool: False (on missing otp).
    """

    interval=settings.OTP_SMS_INTERVAL

    otp = generate_otp_for_user(user_instance, interval=interval)
    if not otp:
        return False

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    # Both 'from_' and 'to' phone numbers must be of format: E.164
    message = client.messages.create(
        body=f'Your OTP code is {otp}. It expires in {interval} seconds.\n\nPlease do not share this code with anyone!',
        from_=str(settings.TWILIO_PHONE_NUMBER), # Must support SMS
        to=str(user_instance.account.phone_number)
    )

    return otp