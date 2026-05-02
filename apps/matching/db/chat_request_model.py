from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class ChatRequest(models.Model):
    """
    A formal chat request that is created when a user swipes 'REQUEST'.
    It tracks whether the other user has accepted or rejected that request.
    When accepted, a Conversation is created.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_chat_requests',
        verbose_name=_('From user')
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_chat_requests',
        verbose_name=_('To user')
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Created at')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated at')
    )

    class Meta:
        verbose_name = _('Chat Request')
        verbose_name_plural = _('Chat Requests')
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['from_user', 'to_user']),
            models.Index(fields=['to_user', 'status']),
        ]

    def __str__(self):
        return f"Request from {self.from_user} to {self.to_user} ({self.get_status_display()})"

    def accept(self):
        """Accept the chat request and create a Conversation if not exists."""
        if self.status != self.Status.PENDING:
            raise ValueError("Cannot accept a non-pending request.")
        self.status = self.Status.ACCEPTED
        self.save(update_fields=['status', 'updated_at'])

        from apps.chat.models import Conversation
        user1, user2 = sorted([self.from_user, self.to_user], key=lambda u: u.id)
        conversation, created = Conversation.objects.get_or_create(
            user1=user1,
            user2=user2
        )
        return conversation

    def reject(self):
        """Reject the chat request."""
        if self.status != self.Status.PENDING:
            raise ValueError("Cannot reject a non-pending request.")
        self.status = self.Status.REJECTED
        self.save(update_fields=['status', 'updated_at'])