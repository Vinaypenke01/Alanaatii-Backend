"""
Custom permissions for Alanaatii Backend.
JWT tokens carry a 'role' claim: 'user', 'writer', 'admin'
"""
from rest_framework.permissions import BasePermission


def get_role(request):
    """Extract role from JWT token payload."""
    token = getattr(request, 'auth', None)
    if token is None:
        return None
    try:
        return token.payload.get('role')
    except AttributeError:
        return None


class IsAdminUser(BasePermission):
    """Only admin users can access."""
    message = 'Access restricted to administrators.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and get_role(request) == 'admin')


class IsWriterUser(BasePermission):
    """Only writer users can access."""
    message = 'Access restricted to writers.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and get_role(request) == 'writer')


class IsCustomerUser(BasePermission):
    """Only customer users can access."""
    message = 'Access restricted to customers.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and get_role(request) == 'user')


class IsAdminOrWriter(BasePermission):
    """Admin or writer access."""
    message = 'Access restricted to administrators and writers.'

    def has_permission(self, request, view):
        role = get_role(request)
        return bool(request.user and request.user.is_authenticated and role in ('admin', 'writer'))


class IsAdminOrCustomer(BasePermission):
    """Admin or customer access."""
    message = 'Access restricted to administrators and customers.'

    def has_permission(self, request, view):
        role = get_role(request)
        return bool(request.user and request.user.is_authenticated and role in ('admin', 'user'))


class IsAnyAuthenticated(BasePermission):
    """Any authenticated user (any role)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminOrReadOnly(BasePermission):
    """Read for all authenticated, write for admin only."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and get_role(request) == 'admin')
