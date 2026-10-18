from rest_framework.decorators import api_view, permission_classes 
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated 
from django.db.models import Q

from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.chat.models import Conversation 
from apps.chat.api.serializers.conversation_list_serializer import ConversationListSerializer 
from apps.utils.custom_rate_limit import custom_ratelimit
from apps.safety.models import Block


@extend_schema(
    summary="My Conversations",
    description="Get list of all conversations for the current user.",
    responses={
        200: ConversationListSerializer(many=True),
        401: OpenApiResponse(description="Authentication required"),
    },
    tags=['Chat']
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='5/5min', method="GET", block=True)
def my_conversations(request):
    """
    GET /api/chat/conversations/
    Returns all conversations the current user is part of.
    """
    blocked_ids = set(Block.objects.filter(blocker=request.user).values_list("blocked_id", flat=True))
    blocked_ids.update(Block.objects.filter(blocked=request.user).values_list("blocker_id", flat=True))
    conversations = Conversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).exclude(user1_id__in=blocked_ids).exclude(user2_id__in=blocked_ids).order_by('-updated_at')

    serializer = ConversationListSerializer(
        conversations,
        many=True,
        context={'request': request}
    )

    return Response(
        {
            "message": "Conversations returned successfully.",
            "data": serializer.data,
            "count": conversations.count()
        },  
        status=status.HTTP_200_OK
    )
