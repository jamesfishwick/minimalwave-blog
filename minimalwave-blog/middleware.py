from django.utils import timezone
import datetime
import re
import math

def reading_time(text):
    """
    Estimate reading time for a given text.
    Average reading speed is about 200-250 words per minute.
    """
    # Strip HTML tags if present
    text = re.sub(r'<[^>]+>', '', text)
    
    # Count words
    words = len(text.split())
    
    # Calculate reading time in minutes (using 200 words per minute)
    minutes = math.ceil(words / 200)
    
    return minutes

class ReadingTimeMiddleware:
    """
    Middleware to add reading time to blog entries and TILs
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            # Add reading time to blog entries
            if 'entry' in response.context_data:
                entry = response.context_data['entry']
                if hasattr(entry, 'body'):
                    response.context_data['reading_time'] = reading_time(entry.body)
            
            # Add reading time to TILs
            if 'til' in response.context_data:
                til = response.context_data['til']
                if hasattr(til, 'body'):
                    response.context_data['reading_time'] = reading_time(til.body)
        
        return response
