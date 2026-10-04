from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.api.serializers.users_serializer import LogoutRequestSerializer, LogoutResponseSerializer
from apps.users.services.tokens import revoke_all_refresh_tokens


@extend_schema(
    summary="Logout from this device",
    description="Blacklist the authenticated user's refresh token. The access token remains valid until its seven-minute expiration.",
    request=LogoutRequestSerializer,
    responses={
        200: LogoutResponseSerializer,
        400: OpenApiResponse(description="The refresh token is invalid, expired, or already revoked"),
        401: OpenApiResponse(description="Authentication required"),
        403: OpenApiResponse(description="The refresh token belongs to another account"),
    },
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_value = request.data.get("refresh")
    if not refresh_value:
        return Response(
            {"error": {"code": "refresh_token_required", "message": "A refresh token is required to log out this device."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = RefreshToken(refresh_value)
        token_user_id = token.get(api_settings.USER_ID_CLAIM)
        if token_user_id is None:
            return Response(
                {"error": {"code": "refresh_token_invalid", "message": "The refresh token does not contain an account identifier."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if str(token_user_id) != str(request.user.pk):
            return Response(
                {"error": {"code": "refresh_token_account_mismatch", "message": "The refresh token does not belong to the authenticated account."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        token.blacklist()
    except TokenError:
        return Response(
            {"error": {"code": "refresh_token_invalid", "message": "The refresh token is invalid, expired, or already revoked."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"message": "Logout successful. Clear the local access and refresh tokens."}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Logout from all devices",
    description="Blacklist all outstanding refresh tokens for the authenticated account. Existing access tokens remain valid until expiration.",
    responses={
        200: LogoutResponseSerializer,
        401: OpenApiResponse(description="Authentication required"),
    },
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_all(request):
    revoke_all_refresh_tokens(request.user)
    return Response(
        {"message": "All refresh tokens were revoked. Clear the local access and refresh tokens on this device."},
        status=status.HTTP_200_OK,
    )
