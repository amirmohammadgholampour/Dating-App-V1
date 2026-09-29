from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    summary="Delete Account",
    description="Delete current user account (soft delete - sets is_active=False).",
    responses={
        204: OpenApiResponse(description="Account deleted successfully"),
        401: OpenApiResponse(description="Authentication required")
    },
    tags=['Users']
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    DELETE /api/users/profile/delete/
    Soft delete the current user's account.
    Tokens remain valid but user cannot interact anymore.
    """
    user = request.user
    user.delete()

    return Response(
        {"message": "Account deleted successfully."},
        status=status.HTTP_204_NO_CONTENT
    )