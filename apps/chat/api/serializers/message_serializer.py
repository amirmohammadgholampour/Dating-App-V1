from rest_framework import serializers
from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from apps.chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'content',
            'sender',
            'sender_name',
            'sent_at',
            'read_at',
            'is_edited',
            'message_type',
            'attachment_name',
            'attachment_url',
            'is_pinned',
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_attachment_url(self, obj):
        if not obj.attachment:
            return None
        return reverse('chat-message-media', kwargs={'message_id': obj.pk})
