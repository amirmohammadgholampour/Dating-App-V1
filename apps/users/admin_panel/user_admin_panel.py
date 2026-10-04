from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from ..models import User
from apps.users.db.user_model import PhoneOTP, UserInterest


class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 1
    fields = ['interest', 'date_added']
    readonly_fields = ['date_added']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'phone_number',
        'phone_verified',
        'email',
        'first_name',
        'last_name',
        'age',
        'city',
        'province',
        'gender',
        'is_online',
        'is_active',
        'is_staff',
    ]
    list_display_links = ['phone_number', 'first_name', 'last_name']

    list_filter = [
        'gender',
        'province',
        'city',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    ]

    search_fields = [
        'phone_number',
        'email',
        'first_name',
        'last_name',
        'city__name',
        'province__name',
    ]

    ordering = ['-date_joined']

    fieldsets = (
        (None, {
            'fields': ('phone_number', 'phone_verified', 'email', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'date_of_birth',
                'age',
                'gender',
                'bio',
                'profile_picture',
                'last_seen_at',
            )
        }),
        ('Location', {
            'fields': ('province', 'city')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    inlines = [UserInterestInline]
    readonly_fields = ['age', 'last_seen_at', 'last_login', 'date_joined']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'phone_verified',
                'email',
                'password1',
                'password2',
                'date_of_birth',
                'gender',
                'province',
                'city',
                'bio',
                'profile_picture',
            ),
        }),
    )

    @admin.display(boolean=True, description='Online')
    def is_online(self, obj):
        return obj.is_online


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'purpose', 'created_at', 'expires_at', 'attempts', 'is_consumed']
    list_filter = ['purpose', 'is_consumed', 'created_at']
    search_fields = ['phone_number']
    readonly_fields = ['phone_number', 'purpose', 'code_digest', 'created_at', 'expires_at', 'attempts', 'is_consumed']
