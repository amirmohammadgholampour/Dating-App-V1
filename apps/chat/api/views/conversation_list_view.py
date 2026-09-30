from rest_framework.decorators import api_view, permission_classes 
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated 
from django.db.models import Q 

from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.chat.models import Conversation 
from apps.chat.api.serializers.conversation_list_serializer import ConversationListSerializer 
from apps.utils.custom_rate_limit import custom_ratelimit


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
    conversations = Conversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).order_by('-updated_at')

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