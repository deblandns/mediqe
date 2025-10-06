from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views
from .views import UserViewSet, UserProfileViewSet, RequestOtpCode

routers = DefaultRouter()
routers.register("users", UserViewSet, basename="users")
routers.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('otp/request/', RequestOtpCode.as_view(), name='otp_request'),
    path("", include(routers.urls))
]