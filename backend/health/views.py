"""
Health check endpoints for monitoring and load balancers.
"""
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if service is running and database is accessible.
    Used by Docker healthcheck, load balancers, and monitoring tools.
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=500)


@require_GET
def readiness_check(request):
    """
    Readiness check endpoint.
    Returns 200 when service is ready to accept traffic.
    Checks database connection and critical dependencies.
    """
    checks = {
        'database': False,
        'redis': False,
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = True
    except Exception:
        pass

    # Check Redis (if available)
    try:
        from django.core.cache import cache
        cache.set('readiness_check', 'ok', timeout=1)
        if cache.get('readiness_check') == 'ok':
            checks['redis'] = True
    except Exception:
        pass

    all_ready = all(checks.values())

    return JsonResponse({
        'status': 'ready' if all_ready else 'not_ready',
        'checks': checks
    }, status=200 if all_ready else 503)
