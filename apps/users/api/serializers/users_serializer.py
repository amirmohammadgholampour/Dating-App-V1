from rest_framework import serializers
from ...models import User, UserInterest, Interest

class GetUserSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = User
        fields = [
            'phone_number', 'password', 'first_name', 'last_name',
            'profile_picture', 'age', 'gender', 'city', 'bio',
            'interests'
        ]


class PostUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    interests = serializers.PrimaryKeyRelatedField(
        queryset=Interest.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'password', 'first_name', 'last_name',
            'profile_picture', 'age', 'gender', 'city', 'bio',
            'interests', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']