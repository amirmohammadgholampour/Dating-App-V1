from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema 

from apps.users.models import User 
from apps.users.api.serializers.user_read_serializer import UserReadSerializer


@swagger_auto_schema(
    method="GET", 
    responses={200: UserReadSerializer}, 
    operation_description="Get the logged-in user profile", 
    operation_summary="My Profile", 
    tags=["Users"]
)
@api_view(["GET"]) 
@permission_classes([IsAuthenticated])
def user_profile(request): 
    req_user = request.user
    user = User.objects.get(id=req_user.id) 
    serializer = UserReadSerializer(user) 
    return Response({
        "message": "User Profile", 
        "data": serializer.data
    }, status=status.HTTP_200_OK) 