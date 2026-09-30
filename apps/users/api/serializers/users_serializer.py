from rest_framework import serializers
from apps.users.models import User, Interest
from django.utils import timezone


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Refresh token to blacklist")

class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=False,
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
            'id', 'email', 'phone_number', 'password', 'first_name', 'last_name',
            'date_of_birth', 'profile_picture', 'age', 'gender', 'city', 'province', 'bio',
            'interests', 'is_active', 'date_joined', 'is_online', 'last_seen_at'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active', 'age', 'is_online', 'last_seen_at']

    def validate_email(self, value):
        return value.lower()

    def validate_date_of_birth(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get('email') and not attrs.get('phone_number'):
            raise serializers.ValidationError("An email address or phone number is required.")
        if attrs.get('phone_number') and self.instance and attrs['phone_number'] != self.instance.phone_number:
            raise serializers.ValidationError({"phone_number": "Phone number cannot be changed here."})
        if attrs.get('email') and self.instance and attrs['email'].lower() != (self.instance.email or '').lower():
            raise serializers.ValidationError({"email": "Email cannot be changed here."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
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
