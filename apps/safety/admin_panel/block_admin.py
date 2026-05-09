from django.contrib import admin
from apps.safety.models import Block


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'blocker',
        'blocked',
        'created_at'
    ]
    list_filter = [
        'created_at',
    ]
    search_fields = [
        'blocker__phone_number',
        'blocker__first_name',
        'blocker__last_name',
        'blocked__phone_number',
        'blocked__first_name',
        'blocked__last_name',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('blocker', 'blocked')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']