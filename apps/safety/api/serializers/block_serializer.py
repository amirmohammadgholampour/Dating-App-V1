from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from apps.safety.models import Block
from apps.users.models import User


class BlockCreateSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source="blocked",
        queryset=User.objects.filter(is_active=True),
    )

    def validate_user_id(self, blocked_user):
        if blocked_user.pk == self.context["request"].user.pk:
            raise serializers.ValidationError("You cannot block yourself.")
        return blocked_user


class BlockedUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="blocked_id", read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = ["id", "user_id", "name", "created_at"]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField())
    def get_name(self, obj):
        return obj.blocked.first_name or f"User {obj.blocked_id}"
