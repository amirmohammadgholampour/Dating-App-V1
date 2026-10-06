from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from django.db.models import (
    Exists, 
    OuterRef, 
    Case, Value, 
    When, 
    IntegerField, 
    F, 
    Q
)
from django.core.paginator import Paginator
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.matching.api.serializers.discover_serializer import DiscoverQuerySerializer, ProfileCardSerializer
from apps.users.models import User, Interest
from apps.matching.models import Swipe, ChatRequest 
from apps.safety.models import Block 
from apps.chat.models import Conversation
from apps.utils.custom_rate_limit import custom_ratelimit


@extend_schema(
    summary="Discover profiles",
    description=(
        "Return eligible profiles for the authenticated user. Results can be filtered by gender, "
        "age range, province, city, or a location name matching either a city or province. "
        "When both city_id and province_id are supplied, the city must belong to that province."
    ),
    parameters=[
        OpenApiParameter(
            name="gender",
            type=str,
            enum=[value for value, _label in User.Gender.choices],
            location=OpenApiParameter.QUERY,
            description="Filter by profile gender.",
        ),
        OpenApiParameter(name="min_age", type=int, location=OpenApiParameter.QUERY, description="Minimum age, inclusive."),
        OpenApiParameter(name="max_age", type=int, location=OpenApiParameter.QUERY, description="Maximum age, inclusive."),
        OpenApiParameter(name="province_id", type=int, location=OpenApiParameter.QUERY, description="Filter by province ID."),
        OpenApiParameter(name="city_id", type=int, location=OpenApiParameter.QUERY, description="Filter by city ID."),
        OpenApiParameter(name="location", type=str, location=OpenApiParameter.QUERY, description="Case-insensitive match against city or province name."),
        OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY, description="Page number (20 profiles per page).", default=1),
    ],
    responses={
        200: inline_serializer(
            name="DiscoverProfilesResponse",
            fields={
                "message": serializers.CharField(),
                "data": ProfileCardSerializer(many=True),
                "page": serializers.IntegerField(),
                "total_pages": serializers.IntegerField(),
                "total_profiles": serializers.IntegerField(),
            },
        ),
        400: OpenApiResponse(description="Invalid filter values."),
        401: OpenApiResponse(description="Authentication required."),
        429: OpenApiResponse(description="Too many Discover requests."),
    },
    tags=["Matching"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='10/min', method="GET", block=True)
def discover_view(request): 
    user = request.user 
    query_serializer = DiscoverQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response(
            {"errors": query_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    filters = query_serializer.validated_data

    # ============================================================
    # STEP 1: Base Queryset
    # ============================================================
    already_swiped_ids = Swipe.objects.filter(
        swiper=user
    ).values_list('swipee_id', flat=True)

    blocked_ids = Block.objects.filter(
        blocker=user
    ).values_list('blocked_id', flat=True)

    blocked_by_ids = Block.objects.filter(
        blocked=user
    ).values_list('blocker_id', flat=True)

    conversation_partner_ids = set()
    my_conversations = Conversation.objects.filter(
        Q(user1=user) | Q(user2=user)
    )
    for conv in my_conversations:
        conversation_partner_ids.add(conv.user1_id)
        conversation_partner_ids.add(conv.user2_id)
    conversation_partner_ids.discard(user.id)

    exclude_ids = (
        set(already_swiped_ids) |
        set(blocked_ids) | 
        set(blocked_by_ids) | 
        conversation_partner_ids |
        {user.id}
    )

    profiles = User.objects.filter(
        is_active=True
    ).exclude(
        id__in=exclude_ids
    )

    if "gender" in filters:
        profiles = profiles.filter(gender=filters["gender"])
    if "min_age" in filters:
        profiles = profiles.filter(age__gte=filters["min_age"])
    if "max_age" in filters:
        profiles = profiles.filter(age__lte=filters["max_age"])
    if "province_id" in filters:
        profiles = profiles.filter(province=filters["province_id"])
    if "city_id" in filters:
        profiles = profiles.filter(city=filters["city_id"])
    if "location" in filters:
        location = filters["location"]
        profiles = profiles.filter(
            Q(city__name__icontains=location) |
            Q(province__name__icontains=location)
        )

    # ============================================================
    # STEP 2: Prioritize Pending Requests
    # ============================================================
    has_requested_me = ChatRequest.objects.filter(
        from_user=OuterRef('pk'),
        to_user=user,
        status='pending'
    )

    profiles = profiles.annotate(
        has_requested_me=Exists(has_requested_me)
    )

    # ============================================================
    # STEP 3: Score Calculation
    # ============================================================
    user_interest_ids = set(
        Interest.objects.filter(
            userinterest__user=user
        ).values_list('id', flat=True)
    )

    profiles = profiles.annotate(
        # Same city: only if user has a city set
        same_city=Case(
            When(
                Q(city__isnull=False) & Q(city=user.city),
                then=Value(3)
            ),
            default=Value(0),
            output_field=IntegerField()
        ),
        # Same province: only if city is different AND user has province set
        same_province=Case(
            When(
                Q(province__isnull=False) &
                Q(province=user.province) &
                ~Q(city=user.city),
                then=Value(1)
            ),
            default=Value(0),
            output_field=IntegerField()
        ),
        # Complete profile: has picture AND bio
        has_complete_profile=Case(
            When(
                Q(profile_picture__isnull=False) &
                Q(bio__isnull=False) &
                ~Q(bio=''),
                then=Value(1)
            ),
            default=Value(0),
            output_field=IntegerField()
        ),
    )

    profiles = profiles.annotate(
        total_score=(
            F('same_city') +
            F('same_province') +
            F('has_complete_profile')
        )
    )

    # ============================================================
    # STEP 4: Calculate Interest Score in Python
    # ============================================================
    profile_list = list(profiles)

    for profile in profile_list:
        profile_interest_ids = set(
            Interest.objects.filter(
                userinterest__user=profile
            ).values_list('id', flat=True)
        )
        common_count = len(user_interest_ids & profile_interest_ids)

        if common_count >= 3:
            profile.total_score += 2
        elif common_count >= 1:
            profile.total_score += 1

    # ============================================================
    # STEP 5: Filter & Sort
    # ============================================================
    # Keep pending requests even with score 0, remove non-pending with score 0
    filtered_profiles = [
        p for p in profile_list
        if p.has_requested_me or p.total_score > 0
    ]

    # Sort: pending first, then score, then date
    filtered_profiles.sort(
        key=lambda p: (not p.has_requested_me, -p.total_score, -p.date_joined.timestamp())
    )

    # ============================================================
    # STEP 6: Pagination
    # ============================================================
    page = filters["page"]
    page_size = 20
    paginator = Paginator(filtered_profiles, page_size)
    page_obj = paginator.get_page(page)

    serializer = ProfileCardSerializer(page_obj.object_list, many=True)

    return Response({
        "message": "Profiles returned successfully",
        "data": serializer.data,
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
        "total_profiles": paginator.count
    }, status=status.HTTP_200_OK)
