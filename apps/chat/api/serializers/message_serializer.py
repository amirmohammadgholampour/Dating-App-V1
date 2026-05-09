from rest_framework import serializers
from apps.chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)

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
        ]
        read_only_fields = fields