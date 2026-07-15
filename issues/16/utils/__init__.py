from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from users.tests import send_test_email

import io, re, base64, requests, stripe, boto3, pyotp, qrcode
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




def get_otp_services_availability():
    otp_services = {'email': False, 'sms': False}

    # Email service

    bool_response, message = send_test_email(
        from_email=settings.EMAIL_HOST_USER,
        to_email=settings.EMAIL_HOST_RECIPIENT_USER,
        subject='MFA Email',
        message="Ignore this email.\n\n"
                "State: Success\n"
                "Framework: Django\n"
                "App: users\n"
                "Call: users.utils - get_otp_services_availability()"
    )
    otp_services['email'] = bool_response

    # SMS service

    number, message = get_mfa_service_number_instance()
    try:
        otp_services['sms'] = number.capabilities.get('sms') is True
    except Exception:
        pass

    return otp_services




def get_mfa_service_number_instance():

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    try:
        numbers = client.incoming_phone_numbers.list(phone_number=settings.TWILIO_PHONE_NUMBER)
        if not numbers:
            return None, 'This Twilio number does not exist in your account.'
        
        number_instance = numbers[0]
        return number_instance, None

    except TwilioRestException as e:
        return None, f'Twilio error {e.status}: {e.msg}'




def email_otp_to_user(user_instance, email=None):
    """
    Generates a time-based one-time password (OTP) using the user's MFA secret and sends it via email.

    This function ensures the user has a stored MFA secret, generates an OTP using TOTP (based on OTP_EMAIL_INTERVAL),
    and delivers it to their registered email address OR email parameter IF provided.

    Args:
        user_instance: A Django User instance.
        email: Must be provided as valid email. (optional)

    Returns:
        str: The generated OTP (on success).
        bool: False (on missing otp).
    """

    interval = settings.OTP_EMAIL_INTERVAL

    otp = generate_otp_for_user(user_instance, interval=interval)
    if not otp:
        return False

    raw_email = email or user_instance.email

    # Send OTP via email
    sender_email = settings.EMAIL_HOST_USER
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It expires in {interval} seconds.\n\nPlease do not share this code with anyone!'
    send_mail(subject, message, sender_email, [raw_email])

    return otp




def sms_otp_to_user(user_instance, phone_number=None):
    """
    Generates a time-based one-time password (OTP) using the user's MFA secret and sends it via SMS.

    This function ensures the user has a stored MFA secret, generates an OTP using TOTP (based on OTP_SMS_INTERVAL),
    and delivers it to their registered in account model - phone number OR phone_number parameter IF provided.

    - Phone numbers must be of E.164 format

    Args:
        user_instance: A Django User instance.
        phone_number : E.164 format phone number. (optional)

    Returns:
        str: The generated OTP (on success).
        bool: False (on missing otp).
    """

    interval = settings.OTP_SMS_INTERVAL

    otp = generate_otp_for_user(user_instance, interval=interval)
    if not otp:
        return False

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    raw_number = phone_number or user_instance.account.phone_number

    # Both 'from_' and 'to' phone numbers must be of format: E.164
    message = client.messages.create(
        body=f'Your OTP code is {otp}. It expires in {interval} seconds.\n\nPlease do not share this code with anyone!',
        # Twilio Phone Number must support SMS (Test numbers cannot send SMS)
        from_=str(settings.TWILIO_PHONE_NUMBER),
        to=str(raw_number)
    )

    return otp




def mask_email(email, visible_chars=1): 
    # Function to mask part of an email address for privacy.
    # 'visible_chars' determines how many characters of the email's name remain visible.

    name, domain = email.split('@')  
    # Splits the email into two parts: 'name' (before @) and 'domain' (after @).

    masked_part = '*' * (len(name) - visible_chars)  
    # Generates a string of '*' characters, masking all but the first 'visible_chars' characters of the name.

    return f"{name[:visible_chars]}{masked_part}@{domain}"  
    # Constructs the masked email by keeping the first 'visible_chars' characters,
    # replacing the rest with '*', and appending the unchanged domain.




def mask_phone_number(phone_number: str) -> str:
    """
    Masks the middle digits of an E.164 formatted phone number.
    Preserves the country code and the last two digits.
    
    Args:
        phone_number (str): The phone number in E.164 format (e.g., +447712345678).
    
    Returns:
        str: Masked phone number (e.g., +44********78).
    """
    match = re.match(r"(\+\d{1,2})(\d+)(\d{2})$", phone_number)
    if not match:
        raise ValueError("Invalid E.164 phone number format")
    
    country_code, middle_part, last_visible = match.groups()
    masked_middle = '*' * len(middle_part)

    return f"{country_code}{masked_middle}{last_visible}"




def set_deletion_date_for_user(user_instance):
    # Note: deletion_date is timezone-aware and saved in UTC
    # The datetime value remains the same
    deletion_date = timezone.now() + timedelta(
        days=settings.DELETE_USER_INTERVAL
    )
    user_instance.account.deletion_date = deletion_date
    user_instance.account.save()




def remove_deletion_date_for_user(user_instance):
    user_instance.account.deletion_date = None
    user_instance.account.save()




PENDING_USER_UPDATES_SESSION = 'pending_user_updates'
def delete_pending_for_update_fields_session(request):
    if PENDING_USER_UPDATES_SESSION in request.session:
        del request.session[PENDING_USER_UPDATES_SESSION]




def save_form_except_pending_for_update_field(request, form_instance, field_name, old_field_str):
    """
    Generates session: PENDING_USER_UPDATES_SESSION
    Stores field changes that require approval before being applied to the database.

    This function handles the workflow where form field changes are not immediately 
    saved to the model. Instead, they are temporarily stored in the session for 
    review/approval before final application.

    The session structure follows a hierarchical format:

    PENDING_USER_UPDATES_SESSION = {
        'ModelName': {
            'model_id': {  # The ID of the model instance being updated (as string)
                'user_id': request.user.id,  # Which user made the update
                'fields': {
                    'field_name': {
                        'new_value': str,
                        'old_value': str,
                        'timestamp': datetime
                    }
                }
            }
        }
    }

    Workflow:
    1. Compares the current form field value with the existing database value
    2. If different, saves the model instance with the OLD value (preserving current state)
    3. Stores the proposed NEW value in the session, grouped by model and object ID
    4. Marks the session as modified to ensure it gets saved

    Args:
        form_instance: Django form instance containing the field data
        field_name: Name of the field being updated
        old_field_str: Current value of the field in the database (as string)
        request: HTTP request object containing the session

    Session Structure:
        - PENDING_USER_UPDATES_SESSION: Main dictionary containing all pending updates
        - model_name: Auto-populated from the model's class name
        - model_id: Primary key of the object being modified (as string)
        - user_id: ID of the user making the update
        - fields: Dictionary containing field-specific updates

    IMPORTANT Note:
        Keep every key as string. This is because this session may get passed
        through the request frequently and may get serialized.
        Hence, model_id and user_id are converted to strings.
    """

    user_id = request.user.id if request.user.is_authenticated else request.session.get('user_id')
    # Error IF no User ID
    if not user_id:
        return JsonResponse({'error': 'User not identified', 'user_id': user_id}, status=400)

    new_field = str(form_instance.cleaned_data.get(field_name))
    if new_field != old_field_str:

        # Save form without updating the field
        form_paused = form_instance.save(commit=False)
        setattr(form_paused, field_name, old_field_str)
        form_paused.save()
        
        # Initialize session
        session_name = PENDING_USER_UPDATES_SESSION
        if session_name not in request.session:
            request.session[session_name] = {}
        
        model_name = form_paused._meta.model.__name__
        model_id = str(form_paused.pk)
        
        # Group by model
        if model_name not in request.session[session_name]:
            request.session[session_name][model_name] = {}
        
        if model_id not in request.session[session_name][model_name]:
            request.session[session_name][model_name][model_id] = {}

        # Link user to pending fields session
        if 'user_id' not in request.session[session_name][model_name][model_id]:
            request.session[session_name][model_name][model_id]['user_id'] = str(user_id)

        # Store field update
        if 'fields' not in request.session[session_name][model_name][model_id]:
            request.session[session_name][model_name][model_id]['fields'] = {}

        request.session[session_name][model_name][model_id]['fields'][field_name] = {
            'new_value': new_field,
            'old_value': old_field_str,
            'timestamp': str(timezone.now())
        }
        request.session.modified = True
        
    else:
        form_instance.save()