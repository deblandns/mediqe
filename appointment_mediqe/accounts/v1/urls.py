from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet

routers = DefaultRouter()
routers.register("users", UserViewSet, basename="users")
routers.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [path("", include(routers.urls))]
