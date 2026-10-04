import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.users.api.serializers.user_read_serializer import UserReadSerializer
from apps.users.api.serializers.users_serializer import EmailRegistrationSerializer, UserSerializer
from apps.users.db.user_model import PhoneOTP, User
from apps.users.services.sms import send_sms
from apps.utils.custom_rate_limit import custom_ratelimit


class EmailPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True, style={"input_type": "password"})


class PhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

    def validate_phone_number(self, value):
        try:
            User.validation_iran_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
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
    update_last_login(None, user)
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": message,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "is_new_user": is_new_user,
        "user": UserReadSerializer(user).data,
    }, status=status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK)


def _error(code, message, http_status, details=None):
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return Response({"error": error}, status=http_status)


def _digest_code(phone_number, purpose, code):
    payload = f"{phone_number}:{purpose}:{code}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), payload, hashlib.sha256).hexdigest()


@extend_schema(summary="Register with email and password", request=EmailRegistrationSerializer,
               responses={201: AuthResponseSerializer, 400: OpenApiResponse(description="Invalid registration data"), 409: OpenApiResponse(description="Email already registered")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="3/5m", method="POST", block=True)
def email_register(request):
    serializer = EmailRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return _error("invalid_registration_data", "Registration data is invalid.", status.HTTP_400_BAD_REQUEST, serializer.errors)
    if User.objects.filter(email__iexact=serializer.validated_data["email"]).exists():
        return _error("email_already_registered", "An account with this email already exists.", status.HTTP_409_CONFLICT)
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
    except IntegrityError:
        return _error("email_already_registered", "An account with this email already exists.", status.HTTP_409_CONFLICT)
    return _token_response(user, is_new_user=True, message="Registration successful. Please complete your profile.")


@extend_schema(summary="Login with email and password", request=EmailPasswordSerializer,
               responses={200: AuthResponseSerializer, 400: OpenApiResponse(description="Invalid login data"), 401: OpenApiResponse(description="Invalid credentials"), 403: OpenApiResponse(description="Inactive account")}, tags=["Users"])
@api_view(["POST"])
@permission_classes([AllowAny])
@custom_ratelimit(key="ip", rate="5/5m", method="POST", block=True)
def email_login(request):
    serializer = EmailPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return _error("invalid_login_data", "Login data is invalid.", status.HTTP_400_BAD_REQUEST, serializer.errors)
    email = serializer.validated_data["email"].strip().lower()
    user_record = User.objects.filter(email__iexact=email).first()
    if user_record and not user_record.is_active:
        return _error("account_inactive", "This account is inactive. Contact support for assistance.", status.HTTP_403_FORBIDDEN)
    user = authenticate(request, email=email, password=serializer.validated_data["password"])
    if user is None:
        return _error("invalid_credentials", "The email or password is incorrect.", status.HTTP_401_UNAUTHORIZED)
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
    ).order_by("-created_at").first()
    if recent_request:
        elapsed = (timezone.now() - recent_request.created_at).total_seconds()
        retry_after = max(1, 60 - int(elapsed))
        return _error(
            "otp_cooldown",
            "A verification code was requested recently. Wait before requesting another code.",
            status.HTTP_429_TOO_MANY_REQUESTS,
            {"retry_after_seconds": retry_after},
        )

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
        return _error("sms_delivery_unavailable", "The verification code could not be sent. Try again later.", status.HTTP_503_SERVICE_UNAVAILABLE)
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
        return _error("invalid_verification_data", "Phone number or verification code format is invalid.", status.HTTP_400_BAD_REQUEST, serializer.errors)
    phone = serializer.validated_data["phone_number"]
    code = serializer.validated_data["code"]
    with transaction.atomic():
        challenge = PhoneOTP.objects.select_for_update().filter(
            phone_number=phone, purpose=purpose, is_consumed=False,
        ).order_by("-created_at").first()
        if not challenge:
            return _error("otp_not_found", "No active verification code was found. Request a new code.", status.HTTP_400_BAD_REQUEST)
        if challenge.expires_at <= timezone.now():
            challenge.is_consumed = True
            challenge.save(update_fields=["is_consumed"])
            return _error("otp_expired", "The verification code has expired. Request a new code.", status.HTTP_400_BAD_REQUEST)
        if challenge.attempts >= 5:
            return _error("otp_attempts_exceeded", "Too many incorrect code attempts. Request a new code.", status.HTTP_429_TOO_MANY_REQUESTS)
        challenge.attempts += 1
        challenge.save(update_fields=["attempts"])
        if not hmac.compare_digest(challenge.code_digest, _digest_code(phone, purpose, code)):
            if challenge.attempts >= 5:
                challenge.is_consumed = True
                challenge.save(update_fields=["is_consumed"])
                return _error("otp_attempts_exceeded", "Too many incorrect code attempts. Request a new code.", status.HTTP_429_TOO_MANY_REQUESTS)
            return _error("otp_invalid", "The verification code is incorrect.", status.HTTP_400_BAD_REQUEST)

        challenge.is_consumed = True
        challenge.save(update_fields=["is_consumed"])
        user = User.objects.filter(phone_number=phone).first()
        is_new_user = purpose == PhoneOTP.Purpose.REGISTER
        if is_new_user and user:
            return _error("phone_already_registered", "This phone number is already registered. Use phone login instead.", status.HTTP_409_CONFLICT)
        if not is_new_user and (user is None or not user.is_active):
            return _error("invalid_or_inactive_account", "No active account is available for this phone number.", status.HTTP_401_UNAUTHORIZED)
        if is_new_user:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(phone_number=phone, phone_verified=True)
            except IntegrityError:
                return _error("phone_already_registered", "This phone number is already registered. Use phone login instead.", status.HTTP_409_CONFLICT)
        elif not user.phone_verified:
            user.phone_verified = True
            user.save(update_fields=["phone_verified"])
    return _token_response(user, is_new_user=is_new_user,
                           message="Registration successful. Please complete your profile." if is_new_user else "Login successful.")
