# apps/chat/views/message.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers

from apps.chat.models import Conversation, Message
from apps.chat.api.serializers.send_message_serializer import SendMessageSerializer
from apps.chat.api.serializers.message_serializer import MessageSerializer
from apps.utils.custom_rate_limit import custom_ratelimit
from apps.safety.services import users_are_blocked


@extend_schema(
    summary="Send Message",
    description="Send a text, image, file, or voice message in a conversation. Attachments use multipart form data.",
    request=SendMessageSerializer,
    responses={
        201: inline_serializer(
            name="SendMessageResponse",
            fields={
                "message": serializers.CharField(),
                "data": MessageSerializer,
            }
        ),
        400: OpenApiResponse(description="Validation error"),
        403: OpenApiResponse(description="Not a member of this conversation"),
        404: OpenApiResponse(description="Conversation not found"),
    },
    tags=['Chat']
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='15/min', method="POST", block=True)
def send_message(request, conversation_id):
    """
    POST /api/chat/conversations/{id}/send/
    Send a text message in a specific conversation.
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
    )

    if request.user not in [conversation.user1, conversation.user2]:
        return Response(
            {"message": "You are not a member of this conversation."},
            status=status.HTTP_403_FORBIDDEN
        )

    recipient = conversation.get_other_user(request.user)
    if users_are_blocked(request.user, recipient):
        return Response(
            {"message": "Messaging is unavailable because one of these users has blocked the other."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = SendMessageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    message = serializer.save(conversation=conversation, sender=request.user)

    return Response(
        {
            "message": "Message sent successfully.",
            "data": {
                **MessageSerializer(message, context={"request": request}).data,
            }
        },
        status=status.HTTP_201_CREATED
    )
