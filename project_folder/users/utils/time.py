from django.utils import timezone
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError




def get_days_until(target_date: date) -> int:
    """
    Returns the number of days from today until target_date.
    If target_date is in the past, returns 0.
    """
    if not target_date:
        return 0
    
    # Note: date() converts datetime to date
    today = datetime.now().date()
    delta = (target_date - today).days
    return max(delta, 0)




def get_current_date_by_timezone(_timezone: str = None) -> datetime:
    try:
        # This line creates a timezone object based on an IANA timezone string
        # (like "Europe/Warsaw", "Asia/Tokyo", or "America/New_York")
        tz = ZoneInfo(_timezone)
        # Returns the current UTC time as a timezone-aware
        utc_now = timezone.now()
        # This converts a timezone-aware UTC datetime (utc_now)
        # into a datetime that's adjusted for the timezone you pass in (tz)
        return utc_now.astimezone(tz)

    except ZoneInfoNotFoundError:
        # Converts that UTC time into the active time zone,
        # as defined by Django settings or middleware
        # (e.g. the user's selected timezone if set).
        return timezone.localtime()