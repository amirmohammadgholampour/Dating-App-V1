# apps/chat/views/message.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.chat.models import Conversation, Message
from apps.chat.api.serializers.message_serializer import SendMessageSerializer


@swagger_auto_schema(
    method="POST",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['content'],
        properties={
            'content': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Message text"
            ),
        }
    ),
    responses={
        201: openapi.Response(
            description="Message sent successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'content': openapi.Schema(type=openapi.TYPE_STRING),
                            'sender_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'sent_at': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                }
            )
        ),
        400: openapi.Response(description="Validation error"),
        403: openapi.Response(description="Not a member of this conversation"),
        404: openapi.Response(description="Conversation not found"),
    },
    operation_description="Send a text message in a conversation.",
    operation_summary="Send Message",
    tags=['Chat']
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
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