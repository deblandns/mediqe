from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views
from .views import UserViewSet, UserProfileViewSet, RequestOtpCode, VerifyOtpRequest

routers = DefaultRouter()
routers.register("users", UserViewSet, basename="users")
routers.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path("token/", jwt_views.TokenObtainPairView.as_view(), name="token_obtain_pair"), # obtain token endpoint
    path("token/refresh/", jwt_views.TokenRefreshView.as_view(), name="token_refresh"), # refresh token endpoint
    path("token/blacklist/", jwt_views.TokenBlacklistView.as_view(), name="token_blacklist"),  # ✅ logout endpoint
    path("otp/request/", RequestOtpCode.as_view(), name="otp_request"), # request OTP code endpoint
    path("otp/verify/", VerifyOtpRequest.as_view(), name="otp_verify"), # verify OTP code endpoint
    path("", include(routers.urls)), # include user and profile routes
]