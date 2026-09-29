from apps.users.api.serializers.users_serializer import LogoutRequestSerializer, LogoutResponseSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework_simplejwt.exceptions import TokenError

from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    summary="Logout",
    description="Logout by blacklisting the refresh token.",
    request=LogoutRequestSerializer,
    responses={
        200: LogoutResponseSerializer,
        400: OpenApiResponse(description="Invalid token"),
        401: OpenApiResponse(description="Authentication required")
    },
    tags=['Users']
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/auth/logout/
    Blacklist the refresh token to prevent further access.
    """
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"message": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK
        )
    except TokenError:
        return Response(
            {"message": "Invalid or expired token."},
            status=status.HTTP_400_BAD_REQUEST
        )