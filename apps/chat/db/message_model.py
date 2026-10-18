from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from pathlib import Path
from uuid import uuid4
from apps.utils.private_storage import private_file_storage


def message_attachment_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"chat_attachments/{instance.conversation_id}/{uuid4().hex}{extension}"


class Message(models.Model):
    """
    Text or private file attachment sent in a conversation.
    """
    class Type(models.TextChoices):
        TEXT = "text", _("Text")
        IMAGE = "image", _("Image")
        FILE = "file", _("File")
        VOICE = "voice", _("Voice")

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
        blank=True,
        default="",
        verbose_name=_("Message content")
    )
    message_type = models.CharField(
        max_length=10,
        choices=Type.choices,
        default=Type.TEXT,
        verbose_name=_("Message type"),
    )
    attachment = models.FileField(
        upload_to=message_attachment_upload_to,
        storage=private_file_storage,
        blank=True,
        null=True,
        verbose_name=_("Private attachment"),
    )
    attachment_name = models.CharField(max_length=255, blank=True, default="")
    attachment_content_type = models.CharField(max_length=100, blank=True, default="")
    is_pinned = models.BooleanField(default=False, verbose_name=_("Is pinned"))
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
