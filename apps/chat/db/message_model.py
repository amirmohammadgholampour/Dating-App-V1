from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Message(models.Model):
    """
    Simple text message in a conversation.
    No images, voice, stickers, or GIFs in MVP.
    """
    conversation = models.ForeignKey(
        'chat.Conversation',
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Conversation")
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_("Sender")
    )
    content = models.TextField(
        max_length=1000,
        verbose_name=_("Message content")
    )
    sent_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Sent at")
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Read at")
    )
    is_edited = models.BooleanField(
        default=False,
        verbose_name=_("Is edited")
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Edited at")
    )

    def __str__(self):
        return f"Message from {self.sender} at {self.sent_at}"