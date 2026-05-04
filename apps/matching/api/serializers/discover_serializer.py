from rest_framework import serializers
from apps.users.models import User


class ProfileCardSerializer(serializers.ModelSerializer):
    """
    Serializer for profile cards shown in Discover.
    Contains only public information needed for swiping.
    """
    interests = serializers.SerializerMethodField()
    province_name = serializers.CharField(source='province.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'age',
            'gender',
            'city_name',
            'province_name',
            'bio',
            'profile_picture',
            'interests',
        ]

    def get_interests(self, obj):
        user_interests = obj.userinterest_set.all().select_related('interest')
        return [ui.interest.name for ui in user_interests]