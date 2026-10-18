from rest_framework import serializers

from apps.utils.upload_validation import validate_identity_video
from apps.users.models import User


class IdentityVideoUploadSerializer(serializers.Serializer):
    video = serializers.FileField(write_only=True)

    def validate_video(self, value):
        try:
            validate_identity_video(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return value


class IdentityVerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["is_verified"]

    def to_internal_value(self, data):
        extra_fields = set(data.keys()) - {"is_verified"}
        if extra_fields:
            raise serializers.ValidationError({field: "Unexpected field." for field in extra_fields})
        return super().to_internal_value(data)
