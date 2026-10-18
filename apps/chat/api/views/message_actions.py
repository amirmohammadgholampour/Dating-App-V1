from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import get_valid_filename
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.chat.api.serializers.message_serializer import MessageSerializer
from apps.chat.api.serializers.edit_message_serializer import EditMessageSerializer
from apps.chat.models import Conversation, Message
from apps.safety.services import users_are_blocked


@extend_schema(
    summary="Edit a message",
    description="Replace the text of a text message or the caption of an attachment message. Only its sender may edit it.",
    request=EditMessageSerializer,
    responses={
        200: MessageSerializer,
        400: OpenApiResponse(description="Validation error."),
        403: OpenApiResponse(description="The message cannot be edited by this user."),
        404: OpenApiResponse(description="Conversation or message not found."),
    },
    tags=["Chat"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def edit_message(request, conversation_id, message_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    if request.user not in (conversation.user1, conversation.user2):
        return Response({"message": "You are not a member of this conversation."}, status=status.HTTP_403_FORBIDDEN)
    if users_are_blocked(conversation.user1, conversation.user2):
        return Response({"message": "This conversation is unavailable because one of these users has blocked the other."}, status=status.HTTP_403_FORBIDDEN)

    message = get_object_or_404(Message, pk=message_id, conversation=conversation)
    if message.sender_id != request.user.pk:
        return Response({"message": "Only the sender can edit this message."}, status=status.HTTP_403_FORBIDDEN)

    serializer = EditMessageSerializer(data=request.data, context={"message": message})
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    message.content = serializer.validated_data["content"]
    message.is_edited = True
    message.edited_at = timezone.now()
    message.save(update_fields=["content", "is_edited", "edited_at"])
    return Response(MessageSerializer(message, context={"request": request}).data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Pin or unpin a message",
    request=None,
    responses={200: MessageSerializer, 403: OpenApiResponse(description="Not allowed to access this conversation."), 404: OpenApiResponse(description="Conversation or message not found.")},
    tags=["Chat"],
)
@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def set_message_pinned(request, conversation_id, message_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    if request.user not in (conversation.user1, conversation.user2):
        return Response({"message": "You are not a member of this conversation."}, status=status.HTTP_403_FORBIDDEN)
    if users_are_blocked(conversation.user1, conversation.user2):
        return Response({"message": "This conversation is unavailable because one of these users has blocked the other."}, status=status.HTTP_403_FORBIDDEN)

    message = get_object_or_404(Message, pk=message_id, conversation=conversation)
    message.is_pinned = request.method == "POST"
    message.save(update_fields=["is_pinned"])
    return Response(MessageSerializer(message, context={"request": request}).data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Download a conversation attachment",
    responses={200: OpenApiResponse(description="Private attachment stream."), 403: OpenApiResponse(description="Conversation access required."), 404: OpenApiResponse(description="Attachment not found.")},
    tags=["Chat"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def message_attachment(request, message_id):
    message = get_object_or_404(Message.objects.select_related("conversation", "sender"), pk=message_id)
    conversation = message.conversation
    if request.user not in (conversation.user1, conversation.user2):
        return Response({"message": "You are not a member of this conversation."}, status=status.HTTP_403_FORBIDDEN)
    if users_are_blocked(conversation.user1, conversation.user2):
        return Response({"message": "This conversation is unavailable because one of these users has blocked the other."}, status=status.HTTP_403_FORBIDDEN)
    if not message.attachment:
        return Response({"message": "This message has no attachment."}, status=status.HTTP_404_NOT_FOUND)

    filename = get_valid_filename(message.attachment_name or "attachment")
    content_type = message.attachment_content_type or "application/octet-stream"
    response = FileResponse(
        message.attachment.open("rb"),
        content_type=content_type,
        as_attachment=message.message_type == Message.Type.FILE,
        filename=filename,
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
