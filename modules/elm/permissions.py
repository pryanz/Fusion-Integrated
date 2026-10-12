from rest_framework.permissions import BasePermission


def get_user_role(user):
    """Return the primary role name string for a user.

    Looks for the role on the user object directly; falls back to checking
    the related profile object that Fusion attaches.
    """
    if hasattr(user, "role"):
        return user.role
    if hasattr(user, "profile") and hasattr(user.profile, "role"):
        return user.profile.role
    return None


class IsHR(BasePermission):
    """Allow access only to users whose role is 'hr' or 'admin'."""

    def has_permission(self, request, view):
        role = get_user_role(request.user)
        return role in ("hr", "admin", "HR", "Admin")


class IsManagerOrHR(BasePermission):
    def has_permission(self, request, view):
        role = get_user_role(request.user)
        return role in ("manager", "hr", "admin", "Manager", "HR", "Admin")


class IsOwnerOrHR(BasePermission):
    def has_object_permission(self, request, view, obj):
        role = get_user_role(request.user)
        if role in ("hr", "admin", "HR", "Admin"):
            return True
        return obj.employee == request.user
