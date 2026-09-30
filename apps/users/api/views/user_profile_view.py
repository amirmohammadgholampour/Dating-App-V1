from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from apps.users.models import User 
from apps.users.api.serializers.user_read_serializer import UserReadSerializer


@extend_schema(
    summary="My Profile",
    description="Get the logged-in user profile",
    responses={200: UserReadSerializer},
    tags=["Users"]
)
@api_view(["GET"]) 
@permission_classes([IsAuthenticated])
def user_profile(request): 
    serializer = UserReadSerializer(request.user)
    return Response({
        "message": "User Profile", 
        "data": serializer.data
    }, status=status.HTTP_200_OK)
