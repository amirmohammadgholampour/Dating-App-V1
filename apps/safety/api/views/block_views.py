from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.safety.api.serializers.block_serializer import (
    BlockCreateSerializer,
    BlockedUserSerializer,
)
from apps.safety.models import Block
from apps.users.models import User


@extend_schema(
    summary="List blocked users",
    responses={200: BlockedUserSerializer(many=True), 401: OpenApiResponse(description="Authentication required.")},
    tags=["Safety"],
)
@extend_schema(
    request=BlockCreateSerializer,
    summary="Block a user",
    responses={201: BlockedUserSerializer, 400: OpenApiResponse(description="Invalid user or self-block."), 401: OpenApiResponse(description="Authentication required.")},
    tags=["Safety"],
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def blocks(request):
    if request.method == "GET":
        queryset = Block.objects.filter(blocker=request.user).select_related("blocked")
        return Response(BlockedUserSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    serializer = BlockCreateSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    block, created = Block.objects.get_or_create(
        blocker=request.user,
        blocked=serializer.validated_data["blocked"],
    )
    response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(
        {
            "message": "User blocked successfully." if created else "User is already blocked.",
            "data": BlockedUserSerializer(block).data,
        },
        status=response_status,
    )


@extend_schema(
    summary="Unblock a user",
    request=None,
    responses={200: OpenApiResponse(description="Block removed."), 404: OpenApiResponse(description="User was not blocked by you.")},
    tags=["Safety"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unblock_user(request, user_id):
    get_object_or_404(User, pk=user_id)
    deleted, _ = Block.objects.filter(blocker=request.user, blocked_id=user_id).delete()
    if not deleted:
        return Response({"message": "This user is not in your block list."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "User unblocked successfully."}, status=status.HTTP_200_OK)
