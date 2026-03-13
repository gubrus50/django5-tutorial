from django.test import TestCase
from django.core.mail import send_mail

# Create your tests here.

def send_test_email(from_email, to_email, subject, message):
    """
    Send test email to a controlled test address
    """

    if from_email is None:
        return False, 'From email address cannot be None'
    if to_email is None:
        return False, 'To email address cannot be None'
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return True, 'Test email sent successfully'

    except Exception as e:
        return False, f'Failed to send test email: {str(e)}'
