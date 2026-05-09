from django_ratelimit.decorators import ratelimit 
from django_ratelimit.exceptions import Ratelimited
from rest_framework import status 
from rest_framework.response import Response 
from functools import wraps 


def custom_ratelimit(key='user', rate='3/5m', method='POST', block=True):
    """
    Custom ratelimit decorator with friendly Persian message.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            try:
                return ratelimit(
                    key=key,
                    rate=rate,
                    method=method,
                    block=block
                )(view_func)(request, *args, **kwargs)
            except Ratelimited:
                return Response(
                    {
                        "message": "Your request limit is over the allowed.",
                        "detail": "Too many requests. Please try again in 5 minutes."
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
        return wrapped_view
    return decorator