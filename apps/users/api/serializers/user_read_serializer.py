from rest_framework import serializers 
from apps.users.models import User 

class UserReadSerializer(serializers.ModelSerializer): 
    interests = serializers.SerializerMethodField()
    province_name = serializers.CharField(source='province.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    is_online = serializers.BooleanField(read_only=True)

    class Meta: 
        model = User
        fields = [
            'id', 'email', 'phone_number', 'phone_verified', 'first_name', 'last_name', 'date_of_birth',
            'profile_picture', 'age', 'gender', 'city_name', 'province_name', 'bio',
            'interests', 'is_online', 'last_seen_at'
        ]

    def get_interests(self, obj):
        user_interests = obj.userinterest_set.all().select_related('interest')
        return [ui.interest.name for ui in user_interests]
