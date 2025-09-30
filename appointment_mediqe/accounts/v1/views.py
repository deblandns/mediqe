from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .serializers import UserSerializer, UserProfileSerializer
from ..models import User, UserProfile
from drf_spectacular.utils import extend_schema


# User View to get http request and handle it
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @extend_schema(
        summary="List all users",
        responses=UserSerializer(many=True),
        description="Retrieve a list of all users.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new user",
        request=UserSerializer,
        responses=UserSerializer,
        description="Create a new user.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a user",
        responses=UserSerializer,
        description="Retrieve a user by ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update a user",
        request=UserSerializer,
        responses=UserSerializer,
        description="Update a user by ID.",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update a user",
        request=UserSerializer,
        responses=UserSerializer,
        description="Partially update a user by ID.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a user", description="Delete a user by ID.")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# UserPofiles View to get http request and handle it
class UserProfileViewSet(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    @extend_schema(
        summary="List all user profiles",
        responses=UserProfileSerializer(many=True),
        description="Retrieve a list of all user profiles.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new user profile",
        request=UserProfileSerializer,
        responses=UserProfileSerializer,
        description="Create a new user profile.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a user profile",
        responses=UserProfileSerializer,
        description="Retrieve a user profile by ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update a user profile",
        request=UserProfileSerializer,
        responses=UserProfileSerializer,
        description="Update a user profile by ID.",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partial update a user profile",
        request=UserProfileSerializer,
        responses=UserProfileSerializer,
        description="Partially update a user profile by ID.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a user profile", description="Delete a user profile by ID."
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
