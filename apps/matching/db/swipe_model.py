from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Swipe(models.Model):
    """
    Records each time a user swipes on another user's profile card.
    - 'REQUEST' means the user tapped the "Request Chat" button.
    - 'REJECT' means the user dismissed the profile (dragged or tapped Reject).
    Once a swipe is recorded, the profile is not shown again.
    """
    class Action(models.TextChoices):
        REQUEST = 'request', _('Request Chat')
        REJECT = 'reject', _('Reject')

    swiper = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='swipes_made',
        verbose_name=_('Swiper')
    )
    swipee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='swipes_received',
        verbose_name=_('Swipee')
    )
    action = models.CharField(
        max_length=10,
        choices=Action.choices,
        verbose_name=_('Action')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Created at')
    )

    class Meta:
        verbose_name = _('Swipe')
        verbose_name_plural = _('Swipes')
        ordering = ['-created_at']
        unique_together = ('swiper', 'swipee') 
        indexes = [
            models.Index(fields=['swiper', 'swipee']),
            models.Index(fields=['swipee', 'action']),
        ]

    def __str__(self):
        return f"{self.swiper} → {self.swipee} ({self.get_action_display()})"