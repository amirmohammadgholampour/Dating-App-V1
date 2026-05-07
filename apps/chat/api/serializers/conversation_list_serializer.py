from rest_framework import serializers
from apps.chat.models import Conversation


class ConversationListSerializer(serializers.ModelSerializer):
    other_user_id = serializers.SerializerMethodField()
    other_user_name = serializers.SerializerMethodField()
    other_user_picture = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'other_user_id',
            'other_user_name',
            'other_user_picture',
            'last_message',
            'unread_count',
            'updated_at',
        ]

    def get_other_user_id(self, obj):
        request = self.context.get('request')
        other = obj.get_other_user(request.user)
        return other.id

    def get_other_user_name(self, obj):
        request = self.context.get('request')
        other = obj.get_other_user(request.user)
        return other.first_name or other.phone_number

    def get_other_user_picture(self, obj):
        request = self.context.get('request')
        other = obj.get_other_user(request.user)
        if other.profile_picture:
            return other.profile_picture.url
        return None

    def get_last_message(self, obj):
        last = obj.get_last_message()
        if last:
            return {
                'content': last.content[:50],
                'sent_at': last.sent_at,
                'is_mine': last.sender == self.context.get('request').user
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        return obj.get_unread_count(request.user)