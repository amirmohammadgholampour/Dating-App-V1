from django.contrib import admin

from apps.matching.models import DiscoverySuggestion


@admin.register(DiscoverySuggestion)
class DiscoverySuggestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "viewer",
        "suggested_user",
        "display_count",
        "last_position",
        "first_suggested_at",
        "last_suggested_at",
    ]
    list_filter = ["first_suggested_at", "last_suggested_at"]
    search_fields = [
        "viewer__phone_number",
        "viewer__first_name",
        "viewer__last_name",
        "suggested_user__phone_number",
        "suggested_user__first_name",
        "suggested_user__last_name",
    ]
    ordering = ["-last_suggested_at"]
    date_hierarchy = "last_suggested_at"
    list_per_page = 50
    readonly_fields = [
        "viewer",
        "suggested_user",
        "first_suggested_at",
        "last_suggested_at",
        "display_count",
        "last_position",
    ]

    fieldsets = (
        (None, {"fields": ("viewer", "suggested_user", "last_position")}),
        (
            "Display history",
            {
                "fields": ("display_count", "first_suggested_at", "last_suggested_at"),
                "classes": ("collapse",),
            },
        ),
    )
