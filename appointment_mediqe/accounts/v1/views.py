import random
from django.core.cache import cache
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from accounts.tasks import send_otp_code
from .serializers import UserSerializer, UserProfileSerializer, OtpCodeRequestSerializer, OtpCodeVerifySerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import User, UserProfile
from ..utils import get_tokens_for_user
from ..permissions import UniversalPermissionMixin, AdminOnlyPermission


# User View to get http request and handle it
class UserViewSet(UniversalPermissionMixin, ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # get the permissions of the user to check wheter is user can access or not
    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]  # direct DRF permission

        return self.get_universal_permissions({
        'list': ['Admin'],
        'create': ['Admin'],
        'retrieve': ['Admin'],
        'update': ['Admin'],
        'partial_update': ['Admin'],
        'destroy': ['Admin'],
    })

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

    @extend_schema(
    summary="Retrieve current authenticated user",
    responses=UserSerializer,
    description="Return details of the currently authenticated user based on JWT token."
    )       
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


# UserPofiles View to get http request and handle it
class UserProfileViewSet(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AdminOnlyPermission] # just for admin users its possible to do crud on UserProfileViewSet

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

# class for getting the otp verification code and save it to ram 
class RequestOtpCode(GenericAPIView):
    """
    View to request OTP code from OTP gateway for both registration and login.
    """
    throttle_scope = 'otp'
    throttle_classes = [ScopedRateThrottle]
    
    serializer_class = OtpCodeRequestSerializer

    @extend_schema(
        summary="Request OTP code",
        request=OtpCodeRequestSerializer,
        responses={
            200: OpenApiResponse(description="Otp Created Successfully"),
            400: OpenApiResponse(description="Otp code already sent"),
            500: OpenApiResponse(description="Failed to generate otp code"),
        },
        description="Request an OTP code for a given phone number.",
    )   
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        # If an OTP is already present, don't re-send
        if cache.get(f"otp:{phone}"):
            return Response(
                {"message": "An OTP has already been sent. Please wait."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # generate OTP and hash it
            otp = str(random.randint(100000, 999999))
            added = cache.add(
                f"otp:{phone}",
                {"otp": make_password(otp), "attempts": 0},
                timeout=300,  # 5 minutes
            )
            if not added:
                return Response(
                    {"message": "An OTP has already been sent. Please wait."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # send OTP async
            send_otp_code.delay(phone, otp)

            # ✅ Unified response for new and existing users to avoid enumeration
            return Response(
                {"message": "If the phone is reachable, an OTP has been sent."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "Failed to generate otp code"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# otp verification class
class VerifyOtpRequest(GenericAPIView):
    """
    View to verify OTP code from OTP gateway.
    Handles both login and registration.
    """
    throttle_scope = 'otp_verify'
    throttle_classes = [ScopedRateThrottle]
    
    serializer_class = OtpCodeVerifySerializer

    @extend_schema(
        summary="Verify OTP code",
        request=OtpCodeVerifySerializer,
        responses={
            200: OpenApiResponse(description="Otp Verified Successfully"),
            400: OpenApiResponse(description="Invalid OTP or Phone number"),
            500: OpenApiResponse(description="Failed to verify otp code"),
        },
        description="Verify an OTP code for a given phone number.",
    )   
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        otp = serializer.validated_data["otp"]
        cached_otp_data = cache.get(f"otp:{phone}")
        try:
            if not cached_otp_data:
                return Response(
                    {"message": "OTP expired or not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if OTP is correct
            if not check_password(otp, cached_otp_data["otp"]):
                cached_otp_data["attempts"] += 1
                cache.set(f"otp:{phone}", cached_otp_data, timeout=300)

                if cached_otp_data["attempts"] >= 3:
                    cache.delete(f"otp:{phone}")
                    return Response(
                        {"message": "Too many attempts. Please request a new OTP."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                return Response(
                    {"message": "Invalid OTP"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ✅ If OTP is correct, delete cache
            cache.delete(f"otp:{phone}")

            # ✅ Create user only if it does not exist (first-time registration)
            user, created = User.objects.get_or_create(phone=phone)
            if created:
                user.set_unusable_password()  # OTP-only account

            user.is_verified = True
            user.save()

            # issue JWT tokens for this user (access + refresh)
            tokens = get_tokens_for_user(user)

            return Response(
                {
                    "message": "OTP verified successfully",
                    "user": {"id": str(user.id), "phone": user.phone},
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
            
        except Exception as e:
            return Response(
                {"message": "Failed to verify otp code"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )