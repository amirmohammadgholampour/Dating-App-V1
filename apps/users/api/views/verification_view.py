from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.users.api.serializers.verification_serializer import (
    IdentityVerificationStatusSerializer,
    IdentityVideoUploadSerializer,
)
from apps.users.models import User


@extend_schema(
    summary="Upload identity verification video",
    request=IdentityVideoUploadSerializer,
    responses={200: OpenApiResponse(description="Video stored privately."), 400: OpenApiResponse(description="Invalid video.")},
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_identity_video(request):
    serializer = IdentityVideoUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    old_video = request.user.identity_video
    old_video_name = old_video.name if old_video else None
    request.user.identity_video = serializer.validated_data["video"]
    request.user.is_verified = False
    request.user.save(update_fields=["identity_video", "is_verified"])

    if old_video_name and old_video_name != request.user.identity_video.name:
        old_video.storage.delete(old_video_name)

    return Response({"message": "Identity video uploaded successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    summary="View a user's identity video (admin only)",
    responses={200: OpenApiResponse(description="Private video stream."), 403: OpenApiResponse(description="Admin access required."), 404: OpenApiResponse(description="Video not found.")},
    tags=["Users"],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_identity_video(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if not user.identity_video:
        return Response({"message": "Identity video not found."}, status=status.HTTP_404_NOT_FOUND)

    extension = user.identity_video.name.rsplit(".", 1)[-1].lower()
    content_types = {"mp4": "video/mp4", "mov": "video/quicktime", "3gp": "video/3gpp", "webm": "video/webm"}
    response = FileResponse(
        user.identity_video.open("rb"),
        content_type=content_types.get(extension, "application/octet-stream"),
        as_attachment=False,
        filename=f"identity-verification.{extension}",
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@extend_schema(
    summary="Set identity verification status (admin only)",
    request=IdentityVerificationStatusSerializer,
    responses={200: IdentityVerificationStatusSerializer, 400: OpenApiResponse(description="Invalid status."), 403: OpenApiResponse(description="Admin access required.")},
    tags=["Users"],
)
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def set_identity_verification(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    serializer = IdentityVerificationStatusSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)
