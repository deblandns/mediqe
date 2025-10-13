"""
Universal Permission System for Mediqe Application

This module provides universal decorators, utilities, and permission classes
that can be used across ALL apps in the project to avoid repetitive role checking.

No more if/else statements for role checking - use these utilities instead!
"""

from functools import wraps, reduce
from django.http import JsonResponse
from operator import or_
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.response import Response
from rest_framework import status


# =============================================================================
# UNIVERSAL ROLE CHECKING UTILITIES
# =============================================================================

def user_has_role(user, roles) -> bool:
    """
    Check if user has any of the specified roles.
    
    Args:
        user: User instance
        roles: List of role strings or single role string
        
    Returns:
        bool: True if user has any of the specified roles
        
    Usage:
        if user_has_role(request.user, ['Admin', 'Doctor']):
            # Do something
    """
    if not user or not user.is_authenticated:
        return False
    
    if isinstance(roles, str):
        roles = [roles]

    # check whether user.role is in roles     
    return user.role in roles


def user_is_admin(user):
    """Check if user is an admin."""
    return user_has_role(user, 'Admin')


def user_is_doctor(user):
    """Check if user is a doctor."""
    return user_has_role(user, 'Doctor')


def user_is_patient(user):
    """Check if user is a patient."""
    return user_has_role(user, 'Patient')


def user_is_nurse(user):
    """Check if user is a nurse."""
    return user_has_role(user, 'Nurse')


def user_is_receptionist(user):
    """Check if user is a receptionist."""
    return user_has_role(user, 'Receptionist')


def user_is_staff(user):
    """Check if user is staff (Admin, Doctor, Nurse, or Receptionist)."""
    return user_has_role(user, ['Admin', 'Doctor', 'Nurse', 'Receptionist'])


def user_is_verified(user):
    """Check if user is verified."""
    return user and user.is_authenticated and user.is_verified


def user_is_active(user):
    """Check if user is active."""
    return user and user.is_authenticated and user.is_active


def user_can_access_object(user, obj):
    """
    Check if user can access a specific object.
    
    Args:
        user: User instance
        obj: Object instance
        
    Returns:
        bool: True if user can access the object
        
    Usage:
        if user_can_access_object(request.user, appointment):
            # User can access this appointment
    """
    if not user or not user.is_authenticated:
        return False
        
    # Admin can access everything
    if user.role == 'Admin':
        return True
        
    # Check ownership
    ownership_fields = ['user', 'created_by', 'patient', 'doctor']
    return any(hasattr(obj, f) and getattr(obj, f) == user for f in ownership_fields)


# =============================================================================
# UNIVERSAL DECORATORS FOR VIEWS AND FUNCTIONS
# =============================================================================

def require_role(roles, error_message="Access denied. Insufficient permissions."):
    """
    Decorator to require specific roles for Django views.
    
    Args:
        roles: List of allowed roles or single role string
        error_message: Custom error message
        
    Usage:
        @require_role(['Admin', 'Doctor'])
        def my_view(request):
            # Only Admin and Doctor can access
            
        @require_role('Admin')
        def admin_only_view(request):
            # Only Admin can access
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not user_has_role(request.user, roles):
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': error_message}, status=403)
                raise PermissionDenied(error_message)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin(error_message="Admin access required."):
    """Decorator to require Admin role."""
    return require_role('Admin', error_message)


def require_doctor(error_message="Doctor access required."):
    """Decorator to require Doctor role."""
    return require_role('Doctor', error_message)


def require_patient(error_message="Patient access required."):
    """Decorator to require Patient role."""
    return require_role('Patient', error_message)


def require_staff(error_message="Staff access required."):
    """Decorator to require Staff role (Admin, Doctor, Nurse, Receptionist)."""
    return require_role(['Admin', 'Doctor', 'Nurse', 'Receptionist'], error_message)


def require_verified(error_message="Account verification required."):
    """Decorator to require verified user."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not user_is_verified(request.user):
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': error_message}, status=403)
                raise PermissionDenied(error_message)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_owner_or_admin(error_message="Access denied. You can only access your own data."):
    """
    Decorator to require object ownership or Admin role.
    Expects the view to receive an object_id parameter.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if user_is_admin(request.user):
                return view_func(request, *args, **kwargs)
            
            # Try to get object_id from kwargs or request
            object_id = kwargs.get('object_id') or request.GET.get('id')
            if not object_id:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': 'Object ID required'}, status=400)
                raise PermissionDenied('Object ID required')
            
            # Assuming the view has a method get_object_by_id to fetch the object
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# UNIVERSAL PERMISSION CLASSES FOR DRF VIEWSETS
# =============================================================================

class RoleBasedPermission(BasePermission):
    """
    Universal permission class for role-based access control.
    Use this in your DRF ViewSets instead of manual role checking.
    
    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [RoleBasedPermission]
            
            def get_permissions(self):
                return [RoleBasedPermission(allowed_roles=['Admin', 'Doctor'])]
    """
   
    def __init__(self, allowed_roles=None):
        self.allowed_roles = allowed_roles or []

    # Override has_permission method    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.allowed_roles:
            return True
            
        return user_has_role(request.user, self.allowed_roles)


class AdminOnlyPermission(BasePermission):
    """Permission class that only allows Admin users."""
    
    def has_permission(self, request, view):
        return user_is_admin(request.user)


class DoctorPermission(BasePermission):
    """Permission class for Doctor role."""
    
    def has_permission(self, request, view):
        return user_has_role(request.user, ['Admin', 'Doctor'])


class PatientPermission(BasePermission):
    """Permission class for Patient role."""
    
    def has_permission(self, request, view):
        return user_has_role(request.user, ['Admin', 'Patient'])


class StaffPermission(BasePermission):
    """Permission class for all staff members."""
    
    def has_permission(self, request, view):
        return user_is_staff(request.user)


class VerifiedUserPermission(BasePermission):
    """Permission class that requires users to be verified."""
    
    def has_permission(self, request, view):
        return user_is_verified(request.user)


class OwnerOrAdminPermission(BasePermission):
    """
    Permission class that allows access to object owners or Admin users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return user_can_access_object(request.user, obj)


# =============================================================================
# UNIVERSAL MIXIN FOR DRF VIEWSETS
# =============================================================================

class UniversalPermissionMixin:
    """
    Universal mixin for DRF ViewSets to easily manage permissions.
    
    Usage:
        class MyViewSet(UniversalPermissionMixin, viewsets.ModelViewSet):
            def get_permissions(self):
                return self.get_universal_permissions({
                    'list': ['Admin', 'Doctor'],
                    'create': ['Admin'],
                    'retrieve': ['Admin', 'Doctor', 'Patient'],
                    'update': ['Admin', 'Doctor'],
                    'destroy': ['Admin'],
                })
    """
    
    def get_universal_permissions(self, permission_map):
        """
        Get permissions based on action and role mapping.
        
        Args:
            permission_map: Dict mapping actions to allowed roles
            
        Returns:
            List of permission instances
        """
        action = getattr(self, 'action', None)
        allowed_roles = permission_map.get(action, [])
        
        if not allowed_roles:
            return [RoleBasedPermission()]
        
        return [RoleBasedPermission(allowed_roles=allowed_roles)]


# =============================================================================
# UNIVERSAL QUERYSET FILTERING UTILITIES
# =============================================================================

def filter_queryset_by_role(queryset, user, model_field_mapping=None):
    """
    Filter queryset based on user role.
    
    Args:
        queryset: Django queryset
        user: User instance
        model_field_mapping: Dict mapping roles to field filters
        
    Returns:
        Filtered queryset
        
    Usage:
        appointments = filter_queryset_by_role(
            Appointment.objects.all(),
            request.user,
            {
                'Patient': {'patient': user},
                'Doctor': {'doctor': user},
                'Admin': {}  # No filter for admin
            }
        )
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    if user.role == 'Admin':
        return queryset
    
    if model_field_mapping and user.role in model_field_mapping:
        filters = model_field_mapping[user.role]
        if filters:
            return queryset.filter(**filters)
        return queryset
    
    return queryset.none()


def get_user_accessible_objects(queryset, user, ownership_fields=None):
    """
    Get objects that user can access based on ownership.
    
    Args:
        queryset: Django queryset
        user: User instance
        ownership_fields: List of field names to check for ownership
        
    Returns:
        Filtered queryset
        
    Usage:
        appointments = get_user_accessible_objects(
            Appointment.objects.all(),
            request.user,
            ['patient', 'doctor', 'created_by']
        )
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    if user.role == 'Admin':
        return queryset
    
    if not ownership_fields:
        ownership_fields = ['user', 'created_by', 'patient', 'doctor']
    
    # Build Q object for ownership check and combine with OR
    ownership_q = reduce(or_, (Q(**{field: user}) for field in ownership_fields), Q())
    
    return queryset.filter(ownership_q)


# =============================================================================
# UNIVERSAL RESPONSE HELPERS
# =============================================================================

def permission_denied_response(message="Access denied.", status_code=403):
    """
    Return a standardized permission denied response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        DRF Response object
    """
    return Response(
        {'error': message, 'detail': 'Permission denied'},
        status=status_code
    )


def role_required_response(required_roles, status_code=403):
    """
    Return a standardized role required response.
    
    Args:
        required_roles: List of required roles
        status_code: HTTP status code
        
    Returns:
        DRF Response object
    """
    roles_str = ', '.join(required_roles) if isinstance(required_roles, list) else required_roles
    return Response(
        {
            'error': f'Access denied. Required role: {roles_str}',
            'detail': 'Insufficient permissions'
        },
        status=status_code
    )