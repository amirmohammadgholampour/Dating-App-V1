# apps/matching/admin.py
from django.contrib import admin
from apps.matching.models import ChatRequest


@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'from_user',
        'to_user',
        'status',
        'created_at',
        'updated_at'
    ]
    list_filter = [
        'status',
        'created_at',
        'updated_at',
    ]
    search_fields = [
        'from_user__phone_number',
        'from_user__first_name',
        'from_user__last_name',
        'to_user__phone_number',
        'to_user__first_name',
        'to_user__last_name',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('from_user', 'to_user', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']