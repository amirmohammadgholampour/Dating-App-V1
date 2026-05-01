from django.db import models 
from django.conf import settings 
from django.utils.translation import gettext_lazy as _ 
from django.utils import timezone 

class Conversation(models.Model):
    """
    One-to-one conversation between two users.
    Created after a chat request is accepted.
    """
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_user1',
        verbose_name=_("First user")
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_user2',
        verbose_name=_("Second user")
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Created at")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at")
    )

    def __str__(self):
        return f"Conversation between {self.user1} and {self.user2}"