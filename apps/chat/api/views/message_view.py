# apps/chat/views/message.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from apps.chat.models import Conversation, Message
from apps.chat.api.serializers.message_serializer import MessageSerializer


class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(
    summary="Get Messages",
    description="Get messages for a conversation (paginated).",
    parameters=[
        OpenApiParameter('page', type=int, description="Page number"),
        OpenApiParameter('page_size', type=int, description="Number of messages per page"),
    ],
    responses={
        200: MessageSerializer(many=True),
        403: OpenApiResponse(description="Not a member of this conversation"),
        404: OpenApiResponse(description="Conversation not found"),
    },
    tags=['Chat']
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_messages(request, conversation_id):
    """
    GET /api/chat/conversations/{id}/messages/
    Returns paginated messages for a specific conversation.
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

    messages = Message.objects.filter(
        conversation=conversation
    ).select_related('sender').order_by('-sent_at')

    paginator = MessagePagination()
    page = paginator.paginate_queryset(messages, request)

    serializer = MessageSerializer(page, many=True)

    return paginator.get_paginated_response(serializer.data)