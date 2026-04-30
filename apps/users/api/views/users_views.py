from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 


from ...models import User 
from ...serializers import (
    UserReadSerializer, 
    UserSerializer
)

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

@swagger_auto_schema(
    method="POST",
    request_body=UserSerializer,
    responses={
        201: openapi.Response(
            description="User is registered successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: "Unvalid data.",
    },
    operation_description="Register a new user with phone number and password.",
    operation_summary="User register",
    tags=['Users']
)
@api_view(["POST"]) 
def register(request): 
    req_user = request.user 
    if req_user.is_authenticated: 
        return Response({
            "message": "You already registered."
        }, status=status.HTTP_400_BAD_REQUEST) 
    
    serializer = UserSerializer(data=request.data) 
    if serializer.is_valid(): 
        user = serializer.save() 
        return Response({
            "message": "You have successfully registered.", 
            "data": UserReadSerializer(user).data
        }, status=status.HTTP_201_CREATED) 
    else: 
        return Response({
            "message": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="put",
    request_body=UserSerializer,
    responses={
        200: openapi.Response(
            description="Profile updated successfully.",
            schema=UserReadSerializer()
        ),
        400: openapi.Response(
            description="Invalid data.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        ),
        401: openapi.Response(description="Authentication required"),
    },
    operation_description="Full profile update. All fields must be provided.",
    operation_summary="Update profile (PUT)",
    tags=['Users']
)
@swagger_auto_schema(
    method="patch",
    request_body=UserSerializer,
    responses={
        200: openapi.Response(
            description="Profile partially updated.",
            schema=UserReadSerializer()
        ),
        400: openapi.Response(description="Invalid data."),
        401: openapi.Response(description="Authentication required"),
    },
    operation_description="Partial profile update. Only send fields to change.",
    operation_summary="Update profile (PATCH)",
    tags=['Users']
)
@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    partial = request.method == "PATCH"
    
    serializer = UserSerializer(
        instance=request.user,
        data=request.data,
        partial=partial
    )
    
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Profile updated successfully",
                "data": UserReadSerializer(user).data
            },
            status=status.HTTP_200_OK
        )
    
    return Response(
        {"errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )