from rest_framework import serializers

from apps.notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor_id",
            "notification_type",
            "message",
            "is_read",
            "created_at",
        ]


class ReadUnreadNotificationsResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    count = serializers.IntegerField()
    data = NotificationSerializer(many=True)
