from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 

from apps.users.api.serializers.user_read_serializer import UserReadSerializer
from apps.users.api.serializers.users_serializer import UserSerializer


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