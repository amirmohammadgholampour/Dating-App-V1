from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework.permissions import BasePermission 
from django.contrib.auth import authenticate 

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 

from ...models import User 
from ...serializers import (
    UserReadSerializer, 
    UserSerializer
)

class NotAuthenticated(BasePermission):
    message = "You are already logged in. Please logout first."
    
    def has_permission(self, request, view):
        return not request.user.is_authenticated

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
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['phone_number', 'password'],
        properties={
            'phone_number': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="11-digit phone number starting with 09"
            ),
            'password': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Password (min 8 chars, letters + numbers)"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Login successful (existing user)",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'is_new_user': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'age': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'gender': openapi.Schema(type=openapi.TYPE_STRING),
                            'city': openapi.Schema(type=openapi.TYPE_STRING),
                            'bio': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                }
            )
        ),
        201: openapi.Response(
            description="Registration successful (new user)",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'is_new_user': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                }
            )
        ),
        400: openapi.Response(description="Invalid data"),
    },
    operation_description=(
        "Login or Register with phone number and password.\n\n"
        "- If user exists and password is correct → returns tokens (200)\n"
        "- If user does not exist → creates account and returns tokens (201)\n"
        "- If user exists but wrong password → returns error (400)"
    ),
    operation_summary="Login or Register",
    tags=['Users']
)
@api_view(["POST"])
@permission_classes([NotAuthenticated])
def login_or_register(request):
    """
    Single endpoint for both login and registration.
    Frontend just sends phone_number + password in both cases.
    """
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    
    # ===== Validation =====
    if not phone_number or not password:
        return Response(
            {"message": "Phone number and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ===== Check if user exists =====
    existing_user = User.objects.filter(phone_number=phone_number).first()
    
    if existing_user:
        # ===== LOGIN =====
        user = authenticate(phone_number=phone_number, password=password)
        
        if user is None:
            return Response(
                {"message": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.is_active:
            return Response(
                {"message": "Your account has been deactivated."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response(
            {
                "message": "Login successful.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "is_new_user": False,
                "user": UserReadSerializer(user).data
            },
            status=status.HTTP_200_OK
        )
    
    else:
        # ===== REGISTER =====
        serializer = UserSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            refresh = RefreshToken.for_user(user)
            
            return Response(
                {
                    "message": "Registration successful. Please complete your profile.",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "is_new_user": True,
                    "user": {
                        "id": user.id,
                        "phone_number": user.phone_number,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "age": user.age,
                        "gender": user.gender,
                        "city": user.city,
                        "bio": user.bio,
                    }
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

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