from rest_framework import serializers
from apps.matching.models import ChatRequest


class ReceivedRequestSerializer(serializers.ModelSerializer):
    from_user_name = serializers.CharField(source='from_user.first_name', read_only=True)
    from_user_age = serializers.IntegerField(source='from_user.age', read_only=True)
    from_user_city = serializers.CharField(source='from_user.city.name', read_only=True)
    from_user_picture = serializers.ImageField(source='from_user.profile_picture', read_only=True)

    class Meta:
        model = ChatRequest
        fields = [
            'id',
            'from_user',
            'from_user_name',
            'from_user_age',
            'from_user_city',
            'from_user_picture',
            'status',
            'created_at',
        ]
        read_only_fields = fields