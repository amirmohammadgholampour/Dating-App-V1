from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from ..models import User
from apps.users.db.user_model import UserInterest


class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 1
    fields = ['interest', 'date_added']
    readonly_fields = ['date_added']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'phone_number',
        'first_name',
        'last_name',
        'age',
        'city',
        'province',
        'gender',
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
        'first_name',
        'last_name',
        'city__name',
        'province__name',
    ]

    ordering = ['-date_joined']

    fieldsets = (
        (None, {
            'fields': ('phone_number', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'age',
                'gender',
                'bio',
                'profile_picture',
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

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'password1',
                'password2',
                'age',
                'gender',
                'province',
                'city',
                'bio',
                'profile_picture',
            ),
        }),
    )