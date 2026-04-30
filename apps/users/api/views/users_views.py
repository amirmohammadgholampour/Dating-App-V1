from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 


from ...models import User 
from ...serializers import GetUserSerializer

@swagger_auto_schema(
    method="GET", 
    responses={200: GetUserSerializer}, 
    operation_description="Get the logged-in user profile", 
    operation_summary="My Profile", 
    tags=["Users"]
)
@api_view(["GET"]) 
@permission_classes([IsAuthenticated])
def user_profile(request): 
    req_user = request.user
    user = User.objects.get(id=req_user.id) 
    serializer = GetUserSerializer(user) 
    return Response({
        "message": "User Profile", 
        "data": serializer.data
    }, status=status.HTTP_200_OK) 