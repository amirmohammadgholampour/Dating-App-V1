from django.db.models import Q

from apps.safety.models import Block


def users_are_blocked(user_a, user_b):
    """Return whether either user has blocked the other."""
    return Block.objects.filter(
        Q(blocker_id=user_a.pk, blocked_id=user_b.pk)
        | Q(blocker_id=user_b.pk, blocked_id=user_a.pk)
    ).exists()
