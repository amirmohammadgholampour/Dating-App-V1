# apps/matching/admin.py
from django.contrib import admin
from apps.matching.models import Swipe


@admin.register(Swipe)
class SwipeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'swiper',
        'swipee',
        'action',
        'created_at'
    ]
    list_filter = [
        'action',
        'created_at',
    ]
    search_fields = [
        'swiper__phone_number',
        'swiper__first_name',
        'swiper__last_name',
        'swipee__phone_number',
        'swipee__first_name',
        'swipee__last_name',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('swiper', 'swipee', 'action')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  
            return self.readonly_fields + ['swiper', 'swipee']
        return self.readonly_fields