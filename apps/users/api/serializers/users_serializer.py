from rest_framework import serializers
from apps.users.models import User, Interest
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class EmailRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True, style={'input_type': 'password'})

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        candidate = User(email=attrs['email'])
        try:
            validate_password(attrs['password'], user=candidate)
        except ValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(min_length=8, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': "The current password is incorrect."})
        if user.check_password(attrs['new_password']):
            raise serializers.ValidationError({'new_password': "The new password must be different from the current password."})
        try:
            validate_password(attrs['new_password'], user=user)
        except ValidationError as exc:
            raise serializers.ValidationError({'new_password': list(exc.messages)})
        return attrs


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Refresh token to blacklist")

class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()



class UserSerializer(serializers.ModelSerializer):
    interests = serializers.PrimaryKeyRelatedField(
        queryset=Interest.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number', 'phone_verified', 'first_name', 'last_name',
            'date_of_birth', 'profile_picture', 'age', 'gender', 'city', 'province', 'bio',
            'interests', 'is_active', 'date_joined', 'is_online', 'last_seen_at'
        ]
        read_only_fields = [
            'id', 'email', 'phone_number', 'phone_verified', 'date_joined',
            'is_active', 'age', 'is_online', 'last_seen_at',
        ]

    def to_internal_value(self, data):
        credential_fields = {'email', 'phone_number', 'phone_verified', 'password'}
        attempted_changes = credential_fields.intersection(data.keys())
        if attempted_changes:
            field = sorted(attempted_changes)[0]
            raise serializers.ValidationError({field: "Account credentials can only be changed through a verification flow."})
        return super().to_internal_value(data)

    def validate_date_of_birth(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def create(self, validated_data):
        raise NotImplementedError("Use the dedicated registration endpoint to create an account.")

    def update(self, instance, validated_data):
        interests = validated_data.pop('interests', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if interests is not None:
            instance.interests.set(interests)
        return instance
