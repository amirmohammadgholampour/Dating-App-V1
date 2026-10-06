from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DiscoverySuggestion(models.Model):
    """Record that a profile was shown to a user in Discover."""
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discovery_suggestions',
        verbose_name=_('Viewer'),
    )
    suggested_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discover_impressions',
        verbose_name=_('Suggested user'),
    )
    first_suggested_at = models.DateTimeField(default=timezone.now, verbose_name=_('First suggested at'))
    last_suggested_at = models.DateTimeField(default=timezone.now, verbose_name=_('Last suggested at'))
    display_count = models.PositiveIntegerField(default=1, verbose_name=_('Display count'))
    last_position = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_('Last position'))

    class Meta:
        verbose_name = _('Discovery suggestion')
        verbose_name_plural = _('Discovery suggestions')
        ordering = ['-last_suggested_at']
        constraints = [
            models.UniqueConstraint(fields=['viewer', 'suggested_user'], name='matching_discovery_unique_pair'),
        ]
        indexes = [
            models.Index(fields=['viewer', '-last_suggested_at'], name='matching_ds_viewer_last_idx'),
            models.Index(fields=['suggested_user', '-last_suggested_at'], name='matching_ds_user_last_idx'),
        ]

    def __str__(self):
        return f"{self.suggested_user} suggested to {self.viewer}"
