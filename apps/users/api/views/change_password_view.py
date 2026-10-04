from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.api.serializers.users_serializer import ChangePasswordSerializer
from apps.users.services.tokens import revoke_all_refresh_tokens
from apps.utils.custom_rate_limit import custom_ratelimit


class ChangePasswordResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


@extend_schema(
    summary="Change password",
    description="Verify the current password, update it, and revoke all sessions. Existing access tokens are rejected immediately.",
    request=ChangePasswordSerializer,
    responses={
        200: ChangePasswordResponseSerializer,
        400: OpenApiResponse(description="The current password is incorrect or the new password is invalid"),
        401: OpenApiResponse(description="Authentication required"),
    },
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate="5/hour", method="POST", block=True)
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        return Response(
            {"error": {"code": "invalid_password_change", "message": "The password change request is invalid.", "details": serializer.errors}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    revoke_all_refresh_tokens(request.user)
    return Response(
        {"message": "Password changed successfully. All sessions were revoked; sign in again."},
        status=status.HTTP_200_OK,
    )
