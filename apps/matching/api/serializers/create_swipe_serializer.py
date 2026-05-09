# apps/matching/serializers/swipe.py
from rest_framework import serializers
from apps.matching.models import Swipe


class CreateSwipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swipe
        fields = ['swipee', 'action']
        extra_kwargs = {
            'swipee': {
                'required': True,
                'help_text': 'ID of the user being swiped on'
            },
            'action': {
                'required': True,
                'help_text': 'request or reject'
            }
        }

    def validate_action(self, value):
        if value not in ['request', 'reject']:
            raise serializers.ValidationError("Action must be 'request' or 'reject'.")
        return value

    def validate(self, data):
        request = self.context.get('request')
        user = request.user

        # Cannot swipe on yourself
        if data['swipee'] == user:
            raise serializers.ValidationError("You cannot swipe on yourself.")

        # Cannot swipe on the same user twice
        if Swipe.objects.filter(swiper=user, swipee=data['swipee']).exists():
            raise serializers.ValidationError("You have already swiped on this user.")

        return data

    def create(self, validated_data):
        validated_data['swiper'] = self.context['request'].user
        return super().create(validated_data)