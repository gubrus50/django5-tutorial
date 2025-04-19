from django.conf import settings
from django.contrib.staticfiles import finders

import json
import os



# AI Generated - Copilot (19/Apr/2025) 

def get_json_data(json_target):
    """Fetch JSON data dynamically based on environment."""
    file_path = None

    if settings.DEBUG:  # Development mode (using staticfiles finders)
        file_path = finders.find(json_target)
    else:  # Production mode (using STATIC_ROOT)
        file_path = os.path.join(settings.STATIC_ROOT, json_target)

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON file '{json_target}': {e}")
            return None
    else:
        print(f"JSON file '{json_target}' not found.")
        return None