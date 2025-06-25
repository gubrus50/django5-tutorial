from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime



# OTP = One-Time Password
# TRED = Throttle Request Expiry-Date
#
OTP_TRED_NAME = getattr(settings, 'OTP_TRED_NAME', 'otp_tred')
#
#
# - Create new expiry date
# expiry = ThrottleOTPRequestExpiryDate.new_date()
#
# -----------------------------------------------------------------------------
#
# Note: 'seconds' are optional, default value is specified at settings.py
#
# - Set in SESSION
# ThrottleOTPRequestExpiryDate.set_session(request, seconds=None)
#
# -----------------------------------------------------------------------------
#
# Note: INHERITS expiry date FROM request session ELSE creates new_date()
#
# - Set in COOKIE
# ThrottleOTPRequestExpiryDate.set_cookie(request, response, seconds=None)
#
# -----------------------------------------------------------------------------
#
# - Get from SESSION
# expiry_date = ThrottleOTPRequestExpiryDate.get(request, source='session')
#
# - Get from COOKIE
# expiry_date = ThrottleOTPRequestExpiryDate.get(request, source='cookie')
#
# -----------------------------------------------------------------------------
#
# - Is session date expired ?
# boolean = ThrottleOTPRequestExpiryDate.has_expired(request)
#
# -----------------------------------------------------------------------------
#
# - Remove from SESSION
# ThrottleOTPRequestExpiryDate.remove_session(request)
#
# - Remove from COOKIE
# ThrottleOTPRequestExpiryDate.remove_cookie(response)
#
#
class ThrottleOTPRequestExpiryDate:
    """
    A utility class for managing OTP throttle expiry dates in Django.
    Provides methods to create, set, get, and remove OTP throttle expiry dates
    in both session and cookie storage.
    """
    
    @staticmethod
    def new_date(seconds=None):
        """
        Generates a new OTP throttle expiry timestamp.
        
        Args:
            seconds (int, optional): 
                The throttle interval in seconds. If not provided, defaults to 
                settings.OTP_REQUEST_THROTTLE_INTERVAL.
                
        Returns:
            str: ISO 8601 formatted timestamp (YYYY-MM-DDTHH:MM:SS.ssssssZ)
        """
        if seconds is None:
            seconds = settings.OTP_REQUEST_THROTTLE_INTERVAL
        return (timezone.now() + timedelta(seconds=seconds)).isoformat()


    @staticmethod
    def set_session(request, seconds=None):
        """
        Sets the OTP throttle expiry date in the session.
        
        Args:
            request: The HTTP request object containing session
            seconds (int, optional): The throttle interval in seconds
                
        Returns:
            HttpRequest: The modified request object with session expiry set
        """
        if seconds is None:
            seconds = settings.OTP_REQUEST_THROTTLE_INTERVAL
        
        request.session[OTP_TRED_NAME] = ThrottleOTPRequestExpiryDate.new_date(seconds)


    @staticmethod
    def set_cookie(request, response, seconds=None):
        """
        Sets the OTP throttle expiry date in a response cookie.
        Prioritizes existing session value if present, otherwise creates new expiry.
        
        Args:
            request: The HTTP request object (checks session first)
            response: The HTTP response object for setting the cookie
            seconds (int, optional): The throttle interval in seconds
        """
        if seconds is None:
            seconds = settings.OTP_REQUEST_THROTTLE_INTERVAL
        
        # Priority: Use existing session value if available
        expiry_date = request.session.get(OTP_TRED_NAME) 
        if not expiry_date:
            expiry_date = ThrottleOTPRequestExpiryDate.new_date(seconds)
        
        response.set_cookie(
            key=OTP_TRED_NAME,
            value=expiry_date,
            max_age=seconds,
            httponly=False, # Hence, allows JavaScript access
            secure=False # Hence, allows HTTP & non-HTTPS transmission
        )


    @staticmethod
    def get(request, source=None):
        """
        Retrieves the OTP throttle expiry date from the specified source.
        
        Args:
            request: The HTTP request object
            source (str): 'session' or 'cookie' specifying where to look
            
        Returns:
            datetime.datetime: The parsed expiry datetime, or None if not found
            
        Raises:
            ValueError: If an invalid source is specified
        """
        expiry_date = None

        if source == 'session':
            expiry_date = request.session.get(OTP_TRED_NAME)
        elif source == 'cookie':
            expiry_date = request.COOKIES.get(OTP_TRED_NAME)
        else:
            raise ValueError(f"Invalid source '{source}'. Expected 'session' or 'cookie'")

        return parse_datetime(expiry_date) if expiry_date else None


    @staticmethod
    def has_expired(request):
        """
        Checks if the OTP throttle period has expired by:
            - retrieving the expiry date from the session and
            - comparing it to the current time.
        If missing or outdated, it's considered expired.
        
        Args:
            request: HttpRequest object to check session/cookie
            
        Returns:
            bool: True if throttle is still active (not expired), False otherwise
        """
        expiry_date = ThrottleOTPRequestExpiryDate.get(request, source='session')

        if not expiry_date or timezone.now() > expiry_date:
            return True
        else:
            return False


    @staticmethod
    def remove_session(request):
        """
        Removes the OTP throttle expiry date from the session.
        Args:
            request: The HTTP request object
        """
        if OTP_TRED_NAME in request.session:
            del request.session[OTP_TRED_NAME]


    @staticmethod
    def remove_cookie(response):
        """
        Removes the OTP throttle expiry date cookie from the response.
        Args:
            response: The HTTP response object
        """
        response.delete_cookie(OTP_TRED_NAME)