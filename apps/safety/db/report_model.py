from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Report(models.Model):
    """
    When a user reports another user for policy violation.
    Reports are reviewed by admins in the admin panel.
    """
    class Reason(models.TextChoices):
        INAPPROPRIATE_CONTENT = 'inappropriate_content', _('Inappropriate Content')
        HARASSMENT = 'harassment', _('Harassment')
        FAKE_PROFILE = 'fake_profile', _('Fake Profile')
        SCAM = 'scam', _('Scam or Fraud')
        SPAM = 'spam', _('Spam')
        OTHER = 'other', _('Other')

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name=_('Reporter')
    )
    reported = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_received',
        verbose_name=_('Reported user')
    )
    reason = models.CharField(
        max_length=30,
        choices=Reason.choices,
        verbose_name=_('Reason')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Additional description')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Created at')
    )

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reporter']),
            models.Index(fields=['reported']),
            models.Index(fields=['reason']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.reporter} reported {self.reported} - {self.get_reason_display()}"