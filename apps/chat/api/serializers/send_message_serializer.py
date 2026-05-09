from rest_framework import serializers
from apps.chat.models import Message


class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content']
        extra_kwargs = {
            'content': {
                'required': True,
                'help_text': 'Message text (max 1000 characters)'
            }
        }

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        if len(value) > 1000:
            raise serializers.ValidationError("Message cannot exceed 1000 characters.")
        return value