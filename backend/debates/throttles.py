from rest_framework.throttling import UserRateThrottle


class DebateGenerationThrottle(UserRateThrottle):
    """
    Custom throttle for debate generation endpoint.
    Limits users to 10 debate generations per hour.
    """
    scope = 'debate_generation'
