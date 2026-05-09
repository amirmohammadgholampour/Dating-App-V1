from rest_framework.permissions import BasePermission

class NotAuthenticated(BasePermission):
    message = "You are already logged in. Please logout first."
    
    def has_permission(self, request, view):
        return not request.user.is_authenticated