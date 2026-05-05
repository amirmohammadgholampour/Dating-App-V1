from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 


@swagger_auto_schema(
    method="delete",
    responses={
        204: openapi.Response(description="Account deleted successfully"),
        401: openapi.Response(description="Authentication required"),
    },
    operation_description="Delete current user account (soft delete - sets is_active=False).",
    operation_summary="Delete Account",
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