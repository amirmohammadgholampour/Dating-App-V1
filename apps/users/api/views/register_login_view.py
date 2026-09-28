from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework_simplejwt.tokens import RefreshToken  
from django.contrib.auth import authenticate 

from django_ratelimit.decorators import ratelimit 
from django_ratelimit.exceptions import Ratelimited

from drf_spectacular.utils import extend_schema, OpenApiResponse

from functools import wraps 

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 

from apps.users.models import User 
from apps.users.api.serializers.user_read_serializer import UserReadSerializer
from apps.users.api.serializers.users_serializer import UserSerializer, LoginRegisterRequestSerializer, LoginRegisterResponseSerializer
from apps.users.api.permissions.not_auth import NotAuthenticated
from apps.utils.custom_rate_limit import custom_ratelimit


@extend_schema(
    summary="Login or Register",
    description=(
        "Login or Register with phone number and password.\n\n"
        "- If user exists and password is correct → returns login success (200)\n"
        "- If user does not exist → creates account and returns tokens (201)\n"
        "- If user exists but wrong password → returns error (400)"
    ),
    request=LoginRegisterRequestSerializer,
    responses={
        200: OpenApiResponse(response=LoginRegisterResponseSerializer, description="Login successful (existing user)"),
        201: OpenApiResponse(response=LoginRegisterResponseSerializer, description="Registration successful (new user)"),
        400: OpenApiResponse(description="Invalid data"),
    },
    tags=['Users']
)
@api_view(["POST"])
@permission_classes([NotAuthenticated])
@custom_ratelimit(key="user", rate='3/5m', method="POST", block=True)
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