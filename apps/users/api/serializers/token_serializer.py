from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password


class UserTokenRefreshSerializer(TokenRefreshSerializer):
    """Reject refresh tokens for inactive, deleted, or password-changed accounts."""

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
        except TokenError as exc:
            raise InvalidToken(str(exc))

        user_id = refresh.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            raise InvalidToken("The refresh token does not contain a user identifier.")

        user_model = get_user_model()
        try:
            user = user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except (user_model.DoesNotExist, ValueError, TypeError) as exc:
            raise AuthenticationFailed("The account associated with this token no longer exists.", code="account_not_found") from exc

        if not user.is_active:
            raise AuthenticationFailed("This account is inactive. Sign in again after it has been reactivated.", code="account_inactive")

        expected_hash = get_md5_hash_password(user.password)
        if refresh.get(api_settings.REVOKE_TOKEN_CLAIM) != expected_hash:
            raise AuthenticationFailed("This refresh token was revoked because the account password changed.", code="token_revoked")

        return super().validate(attrs)
