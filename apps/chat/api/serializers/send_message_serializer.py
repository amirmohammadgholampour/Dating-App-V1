from pathlib import Path

from rest_framework import serializers
from django.utils.text import get_valid_filename

from apps.chat.models import Message
from apps.utils.upload_validation import validate_chat_attachment


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    message_type = serializers.ChoiceField(choices=Message.Type.choices, required=False, default=Message.Type.TEXT)
    attachment = serializers.FileField(required=False, write_only=True, allow_empty_file=False)

    def validate(self, attrs):
        message_type = attrs["message_type"]
        attachment = attrs.get("attachment")
        content = attrs.get("content", "")

        if message_type == Message.Type.TEXT:
            if attachment:
                raise serializers.ValidationError({"attachment": "Text messages cannot include an attachment."})
            if not content.strip():
                raise serializers.ValidationError({"content": "Text messages cannot be empty."})
            return attrs

        if not attachment:
            raise serializers.ValidationError({"attachment": "An attachment is required for this message type."})
        try:
            attrs["attachment_content_type"] = validate_chat_attachment(attachment, message_type)
        except ValueError as exc:
            raise serializers.ValidationError({"attachment": str(exc)})

        safe_name = get_valid_filename(Path(attachment.name).name)[:255]
        if not safe_name:
            raise serializers.ValidationError({"attachment": "Attachment filename is invalid."})
        attrs["attachment_name"] = safe_name
        return attrs

    def create(self, validated_data):
        attachment_content_type = validated_data.pop("attachment_content_type", "")
        attachment_name = validated_data.pop("attachment_name", "")
        message = Message.objects.create(**validated_data)
        if message.attachment:
            message.attachment_name = attachment_name
            message.attachment_content_type = attachment_content_type
            message.save(update_fields=["attachment_name", "attachment_content_type"])
        return message
