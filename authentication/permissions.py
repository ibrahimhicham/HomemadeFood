from rest_framework import permissions
from .models import Chef, Consumer


class UserProfilePermission(permissions.BasePermission):
    """
    Custom permission for user profiles:
    - Consumer can read chef profiles
    - User can read their own profile
    - Chef can update their own profile
    - Consumer can update their own profile
    - Prevent chef from reading consumer profiles
    """

    def has_permission(self, request, view):
        # All actions require authentication
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is the User instance in this case
        target_user = obj
        requesting_user = request.user

        # Allow users to access their own profiles
        if requesting_user.id == target_user.id:
            # Both chefs and consumers can read and update their own profiles
            return True

        # Check if requesting user is a consumer and target is a chef
        if hasattr(requesting_user, 'consumer') and hasattr(target_user, 'chef'):
            # Consumer can read chef profiles
            if request.method in ['GET']:
                return True
            # Consumer cannot update chef profiles
            return False

        # Prevent chef from reading consumer profiles
        if hasattr(requesting_user, 'chef') and hasattr(target_user, 'consumer'):
            # Chef cannot access consumer profiles
            return False

        # For any other combinations, deny access
        return False