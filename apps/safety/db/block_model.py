from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Block(models.Model):
    """
    When a user blocks another user.
    - Blocked user's profile won't be shown to blocker.
    - Existing conversations are hidden.
    - Messages from blocked user are not delivered.
    """
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocks_made',
        verbose_name=_('Blocker')
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocks_received',
        verbose_name=_('Blocked')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Created at')
    )

    class Meta:
        verbose_name = _('Block')
        verbose_name_plural = _('Blocks')
        unique_together = ('blocker', 'blocked')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['blocker', 'blocked']),
            models.Index(fields=['blocked']),
        ]

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"