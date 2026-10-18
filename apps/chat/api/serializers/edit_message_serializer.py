from rest_framework import serializers

from apps.chat.models import Message


class EditMessageSerializer(serializers.Serializer):
    """Accept only a replacement for the message text or attachment caption."""

    content = serializers.CharField(required=True, allow_blank=True, max_length=1000)

    def to_internal_value(self, data):
        unknown_fields = set(data.keys()) - {"content"}
        if unknown_fields:
            raise serializers.ValidationError({
                field: "This field cannot be changed here." for field in unknown_fields
            })
        return super().to_internal_value(data)

    def validate_content(self, value):
        message = self.context["message"]
        if message.message_type == Message.Type.TEXT and not value.strip():
            raise serializers.ValidationError("Text messages cannot be empty.")
        return value
