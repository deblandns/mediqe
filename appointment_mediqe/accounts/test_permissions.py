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