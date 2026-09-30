from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from apps.matching.models import Swipe, ChatRequest 
from apps.matching.api.serializers.create_swipe_serializer import CreateSwipeSerializer
from apps.utils.custom_rate_limit import custom_ratelimit 
from apps.matching.api.serializers.create_swipe_serializer import SwipeRequestSerializer


@extend_schema(
    summary="Create Swipe",
    description="Swipe on a user profile (request chat or reject).",
    request=SwipeRequestSerializer,
    responses={
        201: inline_serializer(
            name="SwipeResponse",
            fields={
                "message": serializers.CharField(),
                "swipe_id": serializers.IntegerField(),
                "action": serializers.CharField(),
                "chat_request_sent": serializers.BooleanField(),
            }
        ),
        400: OpenApiResponse(description="Validation error"),
        401: OpenApiResponse(description="Authentication required"),
    },
    tags=['Matching']
)
@api_view(["POST"]) 
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='30/min', method="POST", block=True)
def create_swipe(request): 
    """
    POST /api/swipe/
    Record a swipe action and create a ChatRequest if action is 'request'.
    """
    serializer = CreateSwipeSerializer(
        data = request.data, 
        context={"request": request} 
    )

    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors,}, 
            status=status.HTTP_400_BAD_REQUEST
        ) 
    
    swipe = serializer.save() 

    chat_request_sent = False 
    if swipe.action == "request": 
        ChatRequest.objects.get_or_create(
            from_user = request.user, 
            to_user = swipe.swipee, 
            defaults={"status": "pending"} 
        )
        chat_request_sent = True 
    
    return Response({
        "message": "Swipe recorded successfully.", 
        "swipe_id": swipe.id, 
        "action": swipe.action,
        "chat_request_sent": chat_request_sent
    }, status=status.HTTP_201_CREATED)