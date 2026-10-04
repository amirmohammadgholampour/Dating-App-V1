from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


@transaction.atomic
def revoke_all_refresh_tokens(user):
    """Blacklist every outstanding refresh token belonging to a user."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
