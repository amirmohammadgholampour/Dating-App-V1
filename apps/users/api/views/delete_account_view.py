from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated
from apps.users.services.tokens import revoke_all_refresh_tokens

from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    summary="Delete Account",
    description="Deactivate the current account and revoke all refresh tokens. Existing access tokens are rejected immediately.",
    responses={
        200: OpenApiResponse(description="Account deactivated and refresh tokens revoked"),
        401: OpenApiResponse(description="Authentication required")
    },
    tags=['Users']
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    Deactivate the current user's account and revoke every refresh token.
    """
    user = request.user
    user.is_active = False
    user.last_seen_at = None
    user.save(update_fields=["is_active", "last_seen_at"])
    revoke_all_refresh_tokens(user)

    return Response(
        {"message": "Account deactivated successfully. All refresh tokens were revoked."},
        status=status.HTTP_200_OK
    )
