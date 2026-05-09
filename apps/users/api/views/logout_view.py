from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework_simplejwt.exceptions import TokenError

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 


@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh'],
        properties={
            'refresh': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Refresh token to blacklist"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Logout successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: openapi.Response(description="Invalid token"),
        401: openapi.Response(description="Authentication required"),
    },
    operation_description="Logout by blacklisting the refresh token.",
    operation_summary="Logout",
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