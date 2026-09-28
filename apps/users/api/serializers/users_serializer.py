from rest_framework import serializers
from apps.users.models import User, Interest
from apps.users.api.serializers.user_read_serializer import UserReadSerializer


class LoginRegisterRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(help_text="11-digit phone number starting with 09")
    password = serializers.CharField(help_text="Password (min 8 chars, letters + numbers)")

class LoginRegisterResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    is_new_user = serializers.BooleanField()
    user = UserReadSerializer()


class UserSerializer(serializers.ModelSerializer):
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
            'profile_picture', 'age', 'gender', 'city', 'province', 'bio',
            'interests', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password')
        interests = validated_data.pop('interests', [])
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if interests:
            user.interests.set(interests)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        interests = validated_data.pop('interests', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if interests is not None:
            instance.interests.set(interests)
        return instance