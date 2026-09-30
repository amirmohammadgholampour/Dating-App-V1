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
from apps.utils.custom_rate_limit import custom_ratelimit


@extend_schema(
    summary="Send Message",
    description="Send a text message in a conversation.",
    request=inline_serializer(
        name="SendMessageRequest",
        fields={"content": serializers.CharField(help_text="Message text")}
    ),
    responses={
        201: inline_serializer(
            name="SendMessageResponse",
            fields={
                "message": serializers.CharField(),
                "data": inline_serializer(
                    name="MessageData",
                    fields={
                        "id": serializers.IntegerField(),
                        "content": serializers.CharField(),
                        "sender_id": serializers.IntegerField(),
                        "sent_at": serializers.CharField(),
                    }
                )
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

    serializer = SendMessageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=serializer.validated_data['content']
    )

    return Response(
        {
            "message": "Message sent successfully.",
            "data": {
                "id": message.id,
                "content": message.content,
                "sender_id": message.sender_id,
                "sent_at": message.sent_at,
            }
        },
        status=status.HTTP_201_CREATED
    )