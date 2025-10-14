# Universal Permission System - Developer Guide

## 🎯 **Purpose**

This universal permission system eliminates the need for repetitive `if/else` statements when checking user roles across your entire project. Instead of writing:

```python
# ❌ DON'T DO THIS ANYMORE
if request.user.role == 'Admin':
    # Admin logic
elif request.user.role == 'Doctor':
    # Doctor logic
elif request.user.role == 'Patient':
    # Patient logic
# ... more if/else statements
```

Use these universal utilities and decorators instead!

## 📁 **Location**

All permission utilities are located in: `appointment_mediqe/accounts/permissions.py`

## 🚀 **Quick Start**

### 1. Import the utilities

```python
from accounts.permissions import (
    user_has_role, user_is_admin, user_is_doctor, user_is_patient,
    require_role, require_admin, require_doctor,
    RoleBasedPermission, AdminOnlyPermission,
    filter_queryset_by_role, get_user_accessible_objects
)
```

### 2. Use in your views

```python
# Instead of: if request.user.role == 'Admin'
if user_is_admin(request.user):
    # Admin logic

# Instead of: if request.user.role in ['Admin', 'Doctor']
if user_has_role(request.user, ['Admin', 'Doctor']):
    # Admin or Doctor logic
```

## 🔧 **Available Utilities**

### **Role Checking Functions**

```python
# Check specific roles
user_is_admin(user)           # True if user is Admin
user_is_doctor(user)          # True if user is Doctor
user_is_patient(user)         # True if user is Patient
user_is_nurse(user)          # True if user is Nurse
user_is_receptionist(user)    # True if user is Receptionist
user_is_staff(user)          # True if user is Admin, Doctor, Nurse, or Receptionist

# Check multiple roles
user_has_role(user, 'Admin')                    # Single role
user_has_role(user, ['Admin', 'Doctor'])       # Multiple roles

# Check user status
user_is_verified(user)       # True if user is verified
user_is_active(user)         # True if user is active

# Check object access
user_can_access_object(user, obj)  # True if user owns the object or is Admin
```

### **Django View Decorators**

```python
from accounts.permissions import require_role, require_admin, require_doctor

# Require specific roles
@require_role(['Admin', 'Doctor'])
def my_view(request):
    # Only Admin and Doctor can access
    pass

@require_admin
def admin_only_view(request):
    # Only Admin can access
    pass

@require_doctor
def doctor_only_view(request):
    # Only Doctor can access
    pass

@require_staff
def staff_only_view(request):
    # Only Admin, Doctor, Nurse, or Receptionist can access
    pass

@require_verified
def verified_users_only(request):
    # Only verified users can access
    pass
```

### **DRF ViewSet Permissions**

```python
from rest_framework import viewsets
from accounts.permissions import (
    RoleBasedPermission, AdminOnlyPermission, DoctorPermission,
    UniversalPermissionMixin
)

# Method 1: Simple permission classes
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOnlyPermission]  # Only Admin can access

# Method 2: Dynamic permissions based on action
class MyViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'list':
            return [RoleBasedPermission(allowed_roles=['Admin', 'Doctor'])]
        elif self.action == 'create':
            return [AdminOnlyPermission()]
        return [RoleBasedPermission()]

# Method 3: Using UniversalPermissionMixin (Recommended)
class MyViewSet(UniversalPermissionMixin, viewsets.ModelViewSet):
    def get_permissions(self):
        return self.get_universal_permissions({
            'list': ['Admin', 'Doctor'],
            'create': ['Admin'],
            'retrieve': ['Admin', 'Doctor', 'Patient'],
            'update': ['Admin', 'Doctor'],
            'destroy': ['Admin'],
        })
```

### **Queryset Filtering**

```python
from accounts.permissions import filter_queryset_by_role, get_user_accessible_objects

# Filter queryset based on user role
def get_queryset(self):
    return filter_queryset_by_role(
        Appointment.objects.all(),
        self.request.user,
        {
            'Patient': {'patient': self.request.user},
            'Doctor': {'doctor': self.request.user},
            'Admin': {}  # No filter for admin
        }
    )

# Filter based on object ownership
def get_queryset(self):
    return get_user_accessible_objects(
        Appointment.objects.all(),
        self.request.user,
        ['patient', 'doctor', 'created_by']
    )
```

## 📋 **Real-World Examples**

### **Example 1: Appointment View**

```python
# appointments/views.py
from accounts.permissions import user_is_doctor, user_is_patient, user_is_admin

class AppointmentView(APIView):
    def get(self, request):
        if user_is_admin(request.user):
            # Admin can see all appointments
            appointments = Appointment.objects.all()
        elif user_is_doctor(request.user):
            # Doctor can see their appointments
            appointments = Appointment.objects.filter(doctor=request.user)
        elif user_is_patient(request.user):
            # Patient can see their appointments
            appointments = Appointment.objects.filter(patient=request.user)
        else:
            return Response({'error': 'Access denied'}, status=403)
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
```

### **Example 2: Medical Record ViewSet**

```python
# medical_records/views.py
from accounts.permissions import UniversalPermissionMixin, filter_queryset_by_role

class MedicalRecordViewSet(UniversalPermissionMixin, viewsets.ModelViewSet):
    serializer_class = MedicalRecordSerializer
    
    def get_permissions(self):
        return self.get_universal_permissions({
            'list': ['Admin', 'Doctor'],
            'create': ['Admin', 'Doctor'],
            'retrieve': ['Admin', 'Doctor', 'Patient'],
            'update': ['Admin', 'Doctor'],
            'destroy': ['Admin'],
        })
    
    def get_queryset(self):
        return filter_queryset_by_role(
            MedicalRecord.objects.all(),
            self.request.user,
            {
                'Patient': {'patient': self.request.user},
                'Doctor': {'doctor': self.request.user},
                'Admin': {}
            }
        )
```

### **Example 3: Django Function View with Decorator**

```python
# dashboards/views.py
from accounts.permissions import require_admin, require_doctor

@require_admin
def admin_dashboard(request):
    # Only Admin can access
    return render(request, 'admin_dashboard.html')

@require_doctor
def doctor_dashboard(request):
    # Only Doctor can access
    return render(request, 'doctor_dashboard.html')
```

### **Example 4: Custom Permission Logic**

```python
# payments/views.py
from accounts.permissions import user_has_role, user_can_access_object

class PaymentView(APIView):
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)
        
        # Check if user can access this payment
        if not user_can_access_object(request.user, payment):
            return Response({'error': 'Access denied'}, status=403)
        
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
```

## 🎨 **Best Practices**

### **1. Use Decorators for Simple Role Checks**

```python
# ✅ Good
@require_admin
def delete_user(request, user_id):
    # Only Admin can delete users
    pass

# ❌ Avoid
def delete_user(request, user_id):
    if request.user.role != 'Admin':
        return Response({'error': 'Access denied'}, status=403)
    # ... rest of code
```

### **2. Use Permission Classes for DRF ViewSets**

```python
# ✅ Good
class MyViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        return self.get_universal_permissions({
            'list': ['Admin', 'Doctor'],
            'create': ['Admin'],
        })

# ❌ Avoid
class MyViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.role not in ['Admin', 'Doctor']:
            return Response({'error': 'Access denied'}, status=403)
        # ... rest of code
```

### **3. Use Utility Functions for Complex Logic**

```python
# ✅ Good
def process_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if user_can_access_object(request.user, appointment):
        # Process appointment
        pass
    else:
        return Response({'error': 'Access denied'}, status=403)

# ❌ Avoid
def process_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if (request.user.role == 'Admin' or 
        appointment.patient == request.user or 
        appointment.doctor == request.user):
        # Process appointment
        pass
    else:
        return Response({'error': 'Access denied'}, status=403)
```

### **4. Filter Querysets Appropriately**

```python
# ✅ Good
def get_queryset(self):
    return filter_queryset_by_role(
        Appointment.objects.all(),
        self.request.user,
        {
            'Patient': {'patient': self.request.user},
            'Doctor': {'doctor': self.request.user},
            'Admin': {}
        }
    )

# ❌ Avoid
def get_queryset(self):
    if self.request.user.role == 'Patient':
        return Appointment.objects.filter(patient=self.request.user)
    elif self.request.user.role == 'Doctor':
        return Appointment.objects.filter(doctor=self.request.user)
    elif self.request.user.role == 'Admin':
        return Appointment.objects.all()
    return Appointment.objects.none()
```

## 🔍 **Common Patterns**

### **Pattern 1: Admin-Only Operations**

```python
# Using decorator
@require_admin
def admin_only_function(request):
    pass

# Using permission class
class AdminOnlyViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOnlyPermission]

# Using utility function
if user_is_admin(request.user):
    # Admin logic
```

### **Pattern 2: Staff-Only Operations**

```python
# Using decorator
@require_staff
def staff_only_function(request):
    pass

# Using permission class
class StaffOnlyViewSet(viewsets.ModelViewSet):
    permission_classes = [StaffPermission]

# Using utility function
if user_is_staff(request.user):
    # Staff logic
```

### **Pattern 3: Owner-Only Operations**

```python
# Using utility function
if user_can_access_object(request.user, obj):
    # User owns this object or is Admin
    pass

# Using permission class
class OwnerOnlyViewSet(viewsets.ModelViewSet):
    permission_classes = [OwnerOrAdminPermission]
```

### **Pattern 4: Role-Specific Queryset Filtering**

```python
def get_queryset(self):
    return filter_queryset_by_role(
        Model.objects.all(),
        self.request.user,
        {
            'Patient': {'patient': self.request.user},
            'Doctor': {'doctor': self.request.user},
            'Nurse': {'nurse': self.request.user},
            'Admin': {}  # No filter
        }
    )
```

## 🧪 **Testing**

### **Test Permission and Decorators**

```python
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import AnonymousUser
from accounts.models import User
from accounts.permissions import RoleBasedPermission


class UniversalPermissionViewSet(viewsets.ViewSet):
    def get_universal_permissions(self, permission_map):
        action = getattr(self, 'action', None)
        allowed_roles = permission_map.get(action, [])

        if not allowed_roles:
            return [RoleBasedPermission()]

        if all(callable(p) and not isinstance(p, str) for p in allowed_roles):
            return [p() for p in allowed_roles]

        return [RoleBasedPermission(allowed_roles=allowed_roles)]

    def get_permissions(self):
        return self.get_universal_permissions({
            'list': ['Admin'],
            'create': ['Admin'],
            'retrieve': ['Admin'],
            'update': ['Admin'],
            'partial_update': ['Admin'],
            'destroy': ['Admin'],
            'me': [IsAuthenticated],
        })

    def list(self, request):
        return Response({'action': 'list'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response({'action': 'me'})


class UniversalPermissionsIntegrationTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UniversalPermissionViewSet.as_view({'get': 'list'})
        self.me_view = UniversalPermissionViewSet.as_view({'get': 'me'})

        self.admin = User.objects.create(phone='09123456789', role='Admin')
        self.patient = User.objects.create(phone='09123456788', role='Patient')
        self.anon = AnonymousUser()

    def test_admin_can_access_list(self):
        request = self.factory.get('/')
        force_authenticate(request, user=self.admin)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_access_list(self):
        request = self.factory.get('/')
        force_authenticate(request, user=self.patient)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_access_me(self):
        request = self.factory.get('/me/')
        force_authenticate(request, user=self.patient)
        response = self.me_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_user_cannot_access_me(self):
        request = self.factory.get('/me/')
        request.user = self.anon
        response = self.me_view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```


## 🚨 **Error Handling**

### **Standard Error Responses**

```python
from accounts.permissions import permission_denied_response, role_required_response

# In your views
if not user_is_admin(request.user):
    return permission_denied_response("Admin access required")

if not user_has_role(request.user, ['Admin', 'Doctor']):
    return role_required_response(['Admin', 'Doctor'])
```

### **Custom Error Messages**

```python
@require_role(['Admin', 'Doctor'], "Only medical staff can access this feature")
def medical_feature(request):
    pass
```

## 📚 **Migration Guide**

### **From Manual Role Checking**

```python
# ❌ Old way
def my_view(request):
    if request.user.role == 'Admin':
        # Admin logic
    elif request.user.role == 'Doctor':
        # Doctor logic
    else:
        return Response({'error': 'Access denied'}, status=403)

# ✅ New way
@require_role(['Admin', 'Doctor'])
def my_view(request):
    if user_is_admin(request.user):
        # Admin logic
    else:
        # Doctor logic
```

### **From DRF Manual Permissions**

```python
# ❌ Old way
class MyViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.role not in ['Admin', 'Doctor']:
            return Response({'error': 'Access denied'}, status=403)
        # ... rest of code

# ✅ New way
class MyViewSet(UniversalPermissionMixin, viewsets.ModelViewSet):
    def get_permissions(self):
        return self.get_universal_permissions({
            'list': ['Admin', 'Doctor'],
        })
```

## 🎯 **Summary**

This universal permission system provides:

1. **Utility Functions**: `user_is_admin()`, `user_has_role()`, etc.
2. **Decorators**: `@require_admin`, `@require_role()`, etc.
3. **Permission Classes**: `AdminOnlyPermission`, `RoleBasedPermission`, etc.
4. **Queryset Filtering**: `filter_queryset_by_role()`, `get_user_accessible_objects()`
5. **Response Helpers**: `permission_denied_response()`, `role_required_response()`

**Benefits:**
- ✅ No more repetitive `if/else` statements
- ✅ Consistent permission logic across the project
- ✅ Easy to maintain and update
- ✅ Type-safe and well-documented
- ✅ Testable components
- ✅ Works with both Django views and DRF ViewSets

**Start using these utilities today and make your code cleaner and more maintainable!**
