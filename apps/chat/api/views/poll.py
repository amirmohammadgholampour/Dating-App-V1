from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.utils import timezone 

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.chat.models import Conversation, Message
from apps.chat.api.serializers.message_serializer import MessageSerializer
from apps.utils.custom_rate_limit import custom_ratelimit


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            'after',
            openapi.IN_QUERY,
            description="ISO datetime string (e.g., 2026-05-09T10:00:00). Only messages after this time.",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: openapi.Response(
            description="New messages returned",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'messages': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'has_new': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'server_time': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: openapi.Response(description="Missing or invalid 'after' parameter"),
        403: openapi.Response(description="Not a member"),
        404: openapi.Response(description="Conversation not found"),
    },
    operation_description="Poll for new messages after a timestamp.",
    operation_summary="Poll Messages",
    tags=['Chat']
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='20/min', method="GET", block=True)
def poll_messages(request, conversation_id):
    """
    GET /api/chat/conversations/{id}/poll/?after=2026-05-09T10:00:00
    Return messages sent after the given timestamp.
    """
    after_param = request.query_params.get('after')

    if not after_param:
        return Response(
            {"message": "Parameter 'after' is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    after_datetime = parse_datetime(after_param)
    if not after_datetime:
        return Response(
            {"message": "Invalid datetime format. Use ISO format (e.g., 2026-05-09T10:00:00)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in [conversation.user1, conversation.user2]:
        return Response(
            {"message": "You are not a member of this conversation."},
            status=status.HTTP_403_FORBIDDEN
        )

    messages = Message.objects.filter(
        conversation=conversation,
        sent_at__gt=after_datetime
    ).exclude(
        sender=request.user
    ).select_related('sender').order_by('sent_at')

    serializer = MessageSerializer(messages, many=True)

    return Response(
        {
            "messages": serializer.data,
            "has_new": messages.exists(),
            "server_time": timezone.now().isoformat(),
        },
        status=status.HTTP_200_OK
    )