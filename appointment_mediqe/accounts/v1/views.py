import random
from django.core.cache import cache
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from accounts.tasks import send_otp_code
from .serializers import UserSerializer, UserProfileSerializer, OtpCodeRequest, OtpCodeVerify
from ..models import User, UserProfile
from ..utils import get_tokens_for_user
from drf_spectacular.utils import extend_schema, OpenApiResponse


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


# class for getting the otp verification code and save it to ram
class RequestOtpCode(GenericAPIView):
    """
    view to request otp code from otp gateway and singing up
    """
    # scoped rate throttling for rate limiting request for singup
    throttle_scope = 'otp'
    throttle_classes = [ScopedRateThrottle]
    
    
    serializer_class = OtpCodeRequest

    @extend_schema(
        summary="Request OTP code",
        request=OtpCodeRequest,
        responses={
            200: OpenApiResponse(description="Otp Created Successfully"),
            400: OpenApiResponse(description="Phone number already exists or Otp code already sent"),
            500: OpenApiResponse(description="Failed to generate otp code"),
        },
        description="Request an OTP code for a given phone number.",
    )   
    # check if the phone number is available or not and do the rest logic of otp code request
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        if User.objects.filter(
            phone=phone
        ).exists():  # if user is available inside our database
            return Response(
                {"message": "Phone number already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            if cache.get(f"otp:{phone}"):
                return Response(
                    {"message": "Otp code already sent"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                otp = str(random.randint(100000, 999999))
                send_otp_code.delay(phone, otp)
                # set the cache data into a redis database
                cache.set(
                    f"otp:{phone}",
                    {
                        "otp": make_password(otp),
                        "attempts": 0,
                    },
                    timeout=300,
                )  # 5 minutes
            return Response(
                {"message": "Otp Created Successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "Failed to generate otp code"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# otp verification class
class VerifyOtpRequest(GenericAPIView):
    """
    view to verify otp code from otp gateway and singing up
    """
    # Flow:
    # 1. Client posts phone + otp to this endpoint.
    # 2. If OTP matches, we delete the cached OTP, create the User if
    #    not present, mark them as verified, and return JWT access +
    #    refresh tokens using `get_tokens_for_user` from
    #    `accounts.utils`.
    # 3. If too many failed attempts or OTP expired, return 400 with
    #    an appropriate message.

    # scoped rate throttling for rate limiting request for singup
    throttle_scope = 'otp_verify'
    throttle_classes = [ScopedRateThrottle]
    
    
    serializer_class = OtpCodeVerify

    @extend_schema(
        summary="Verify OTP code",
        request=OtpCodeVerify,
        responses={
            200: OpenApiResponse(description="Otp Verified Successfully"),
            400: OpenApiResponse(description="Invalid OTP or Phone number"),
            500: OpenApiResponse(description="Failed to verify otp code"),
        },
        description="Verify an OTP code for a given phone number.",
    )   
    # check if the phone number is available or not and do the rest logic of otp code verification
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

            # Check if OTP is correct using Django's hasher
            if not check_password(otp, cached_otp_data["otp"]):
                # Increment failed attempt count
                cached_otp_data["attempts"] += 1
                cache.set(f"otp:{phone}", cached_otp_data, timeout=300)

                # If too many failed attempts
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

            # ✅ If OTP is correct
            cache.delete(f"otp:{phone}")

            # Create the user if it doesn't exist yet. We use the custom
            user, created = User.objects.get_or_create(phone=phone)
            if created:
                user.set_unusable_password() # newly created OTP-only user should have unusable password
            user.is_verified = False
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