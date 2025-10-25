"""
Custom exception handlers for better API error messages.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats throttle errors with user-friendly messages.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle throttle errors specially
    if isinstance(exc, Throttled):
        wait_seconds = exc.wait

        # Convert seconds to human-readable format
        if wait_seconds < 60:
            wait_time = f"{int(wait_seconds)} seconds"
        elif wait_seconds < 3600:
            minutes = int(wait_seconds / 60)
            wait_time = f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = int(wait_seconds / 3600)
            minutes = int((wait_seconds % 3600) / 60)
            if minutes > 0:
                wait_time = f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                wait_time = f"{hours} hour{'s' if hours != 1 else ''}"

        custom_response_data = {
            'error': 'rate_limit_exceeded',
            'message': f"You've made too many requests. Please try again in {wait_time}.",
            'retry_after_seconds': int(wait_seconds),
            'retry_after_display': wait_time,
        }

        response = Response(custom_response_data, status=429)
        response['Retry-After'] = int(wait_seconds)

    return response
