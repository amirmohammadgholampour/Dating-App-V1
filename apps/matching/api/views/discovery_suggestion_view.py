from django.db import transaction
from django.db.models import F
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.matching.api.serializers.discover_serializer import (
    SaveSuggestionsResponseSerializer,
    SaveSuggestionsSerializer,
)
from apps.matching.models import DiscoverySuggestion
from apps.users.models import User
from apps.utils.custom_rate_limit import custom_ratelimit


@extend_schema(
    summary="Save Discover suggestions",
    description=(
        "Record profiles displayed in a Discover page for the authenticated user. "
        "Send the profile IDs returned in that page; saving a profile again updates its "
        "last shown time, position, and display count."
    ),
    request=SaveSuggestionsSerializer,
    responses={
        201: SaveSuggestionsResponseSerializer,
        400: OpenApiResponse(description="Invalid, inactive, or self profile ID."),
        401: OpenApiResponse(description="Authentication required."),
        429: OpenApiResponse(description="Too many requests."),
    },
    tags=["Matching"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate="30/min", method="POST", block=True)
def save_discovery_suggestions(request):
    """Record the profiles returned to the user by a Discover page."""
    serializer = SaveSuggestionsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile_ids = serializer.validated_data["profile_ids"]
    profiles = User.objects.filter(id__in=profile_ids, is_active=True)
    profiles_by_id = {profile.id: profile for profile in profiles}
    unavailable_ids = [
        profile_id
        for profile_id in profile_ids
        if profile_id == request.user.id or profile_id not in profiles_by_id
    ]
    if unavailable_ids:
        return Response(
            {
                "errors": {
                    "profile_ids": (
                        "Profiles must exist, be active, and must not include the current user. "
                        f"Invalid IDs: {unavailable_ids}."
                    )
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    with transaction.atomic():
        for position, profile_id in enumerate(profile_ids, start=1):
            suggestion, created = DiscoverySuggestion.objects.get_or_create(
                viewer=request.user,
                suggested_user=profiles_by_id[profile_id],
                defaults={
                    "first_suggested_at": now,
                    "last_suggested_at": now,
                    "last_position": position,
                },
            )
            if not created:
                DiscoverySuggestion.objects.filter(pk=suggestion.pk).update(
                    last_suggested_at=now,
                    display_count=F("display_count") + 1,
                    last_position=position,
                )

    return Response(
        {
            "message": "Discover suggestions saved successfully.",
            "saved_count": len(profile_ids),
            "profile_ids": profile_ids,
        },
        status=status.HTTP_201_CREATED,
    )
