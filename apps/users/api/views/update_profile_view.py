from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from apps.users.api.serializers.user_read_serializer import UserReadSerializer
from apps.users.api.serializers.users_serializer import UserSerializer
from apps.utils.custom_rate_limit import custom_ratelimit

from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    summary="Update profile (PUT)",
    description="Update profile fields. Age is calculated from date_of_birth and cannot be set directly.",
    request=UserSerializer,
    responses={
        200: UserReadSerializer, 
        400: OpenApiResponse(description="Invalid data"),
        401: OpenApiResponse(description="Authentication required")
    },
    tags=['Users']
)

@extend_schema(
    summary="Update profile (PATCH)",
    description="Partial profile update. Only send fields to change.",
    request=UserSerializer,
    responses={
        200: UserReadSerializer,
        400: OpenApiResponse(description="Invalid data."),
        401: OpenApiResponse(description="Authentication required"),
    },
    tags=['Users']
)
@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='5/min', method="PUT", block=True)
@custom_ratelimit(key="user", rate='5/min', method="PATCH", block=True)
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
