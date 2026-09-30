import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.users.api.serializers.user_read_serializer import UserReadSerializer
from apps.users.api.serializers.users_serializer import UserSerializer
from apps.users.db.user_model import PhoneOTP, User
from apps.users.services.sms import send_sms
from apps.utils.custom_rate_limit import custom_ratelimit


class EmailPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True, style={"input_type": "password"})


class PhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

    def validate_phone_number(self, value):
        User.validation_iran_phone_number(value)
        return value


class PhoneCodeSerializer(PhoneSerializer):
    code = serializers.RegexField(r"^\d{6}$")


class AuthResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    is_new_user = serializers.BooleanField()
    user = UserReadSerializer()


def _token_response(user, *, is_new_user=False, message="Login successful."):
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": message,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "is_new_user": is_new_user,
        "user": UserReadSerializer(user).data,
    }, status=status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK)


def _digest_code(phone_number, purpose, code):
    payload = f"{phone_number}:{purpose}:{code}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), payload, hashlib.sha256).hexdigest()


@extend_schema(summary="Register with email and password", request=UserSerializer,
               responses={201: AuthResponseSerializer, 400: OpenApiResponse(description="Invalid or existing account")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="3/5m", method="POST", block=True)
def email_register(request):
    serializer = UserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    if not serializer.validated_data.get("email") or not serializer.validated_data.get("password"):
        return Response({"message": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email__iexact=serializer.validated_data["email"]).exists():
        return Response({"message": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    return _token_response(user, is_new_user=True, message="Registration successful. Please complete your profile.")


@extend_schema(summary="Login with email and password", request=EmailPasswordSerializer,
               responses={200: AuthResponseSerializer, 400: OpenApiResponse(description="Invalid credentials")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="5/5m", method="POST", block=True)
def email_login(request):
    serializer = EmailPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, email=serializer.validated_data["email"], password=serializer.validated_data["password"])
    if user is None:
        return Response({"message": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)
    return _token_response(user)


def _request_phone_code(request, purpose):
    serializer = PhoneSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    phone = serializer.validated_data["phone_number"]
    exists = User.objects.filter(phone_number=phone).exists()
    # Use identical responses for known and unknown numbers to limit account discovery.
    allowed = exists if purpose == PhoneOTP.Purpose.LOGIN else not exists
    if not allowed:
        return Response({"message": "If this number can use this action, a verification code will be sent."}, status=status.HTTP_200_OK)
    recent_request = PhoneOTP.objects.filter(
        phone_number=phone, purpose=purpose,
        created_at__gt=timezone.now() - timedelta(seconds=60),
    ).exists()
    if recent_request:
        return Response({"message": "If this number can use this action, a verification code will be sent."}, status=status.HTTP_200_OK)

    code = f"{secrets.randbelow(1_000_000):06d}"
    PhoneOTP.objects.filter(phone_number=phone, purpose=purpose, is_consumed=False).update(is_consumed=True)
    challenge = PhoneOTP.objects.create(
        phone_number=phone,
        purpose=purpose,
        code_digest=_digest_code(phone, purpose, code),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    try:
        send_sms(phone, f"Your verification code is {code}. It expires in 5 minutes.")
    except (ImproperlyConfigured, RuntimeError):
        challenge.delete()
        return Response({"message": "Phone verification is temporarily unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({"message": "If this number can use this action, a verification code will be sent."}, status=status.HTTP_200_OK)


@extend_schema(summary="Request a phone registration code", request=PhoneSerializer,
               responses={200: OpenApiResponse(description="Request accepted"), 400: OpenApiResponse(description="Invalid phone")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="3/5m", method="POST", block=True)
def phone_register_request_code(request):
    return _request_phone_code(request, PhoneOTP.Purpose.REGISTER)


@extend_schema(summary="Verify phone registration code", request=PhoneCodeSerializer,
               responses={201: AuthResponseSerializer, 400: OpenApiResponse(description="Invalid or expired code")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="5/5m", method="POST", block=True)
def phone_register_verify_code(request):
    return _verify_phone_code(request, PhoneOTP.Purpose.REGISTER)


@extend_schema(summary="Request a phone login code", request=PhoneSerializer,
               responses={200: OpenApiResponse(description="Request accepted"), 400: OpenApiResponse(description="Invalid phone")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="3/5m", method="POST", block=True)
def phone_login_request_code(request):
    return _request_phone_code(request, PhoneOTP.Purpose.LOGIN)


@extend_schema(summary="Verify phone login code", request=PhoneCodeSerializer,
               responses={200: AuthResponseSerializer, 400: OpenApiResponse(description="Invalid or expired code")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="5/5m", method="POST", block=True)
def phone_login_verify_code(request):
    return _verify_phone_code(request, PhoneOTP.Purpose.LOGIN)


def _verify_phone_code(request, purpose):
    serializer = PhoneCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    phone = serializer.validated_data["phone_number"]
    code = serializer.validated_data["code"]
    with transaction.atomic():
        challenge = PhoneOTP.objects.select_for_update().filter(
            phone_number=phone, purpose=purpose, is_consumed=False,
            expires_at__gt=timezone.now(), attempts__lt=5,
        ).order_by("-created_at").first()
        if not challenge:
            return Response({"message": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)
        challenge.attempts += 1
        challenge.save(update_fields=["attempts"])
        if not hmac.compare_digest(challenge.code_digest, _digest_code(phone, purpose, code)):
            return Response({"message": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=phone).first()
        is_new_user = purpose == PhoneOTP.Purpose.REGISTER
        if is_new_user and user:
            return Response({"message": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)
        if not is_new_user and (user is None or not user.is_active):
            return Response({"message": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)
        if is_new_user:
            user = User.objects.create_user(phone_number=phone)
        challenge.is_consumed = True
        challenge.save(update_fields=["is_consumed"])
    return _token_response(user, is_new_user=is_new_user,
                           message="Registration successful. Please complete your profile." if is_new_user else "Login successful.")
