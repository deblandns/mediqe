from rest_framework import serializers
from django.core.validators import RegexValidator
from ..models import User, UserProfile


# custom user serializer to serilize data of user
class UserSerializer(serializers.ModelSerializer):
    # make the password for otp based
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={"input_type": "password", "placeholder": "Password"},
    )

    class Meta:
        model = User
        fields = "__all__"
        # read only fields
        read_only_fields = ("group", "permissions")

    # set user password in a hashed way correctly when creating new user
    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # otp only accounts
        user.save()
        return user

    # set password of user when updating the user
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)

    class Meta:
        model = UserProfile
        fields = "__all__"

    # create User profile for user for the first time (This logic is correct!)
    def create(self, validated_data):
        # This will now correctly receive the 'user' data because of the field definition above
        user_data = validated_data.pop("user")
        password = user_data.pop("password", None)
        user = User(**user_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # only otp accounts
        user.save()
        profile = UserProfile.objects.create(user=user, **validated_data)
        return profile

    # update the user profile based on the user and user profile data (This logic is correct!)
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data:
            password = user_data.pop("password", None)
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            if password:
                instance.user.set_password(password)
            instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# class to serialize and validate the number input from user
class OtpCodeRequest(serializers.Serializer):
    """
    this serializer will check if the number is valid or not then send it as json code
    """

    phone = serializers.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r"^(\+98|0)?9\d{9}$",
                message="Please enter a valid Iranian mobile number (e.g., 09123456789 or +989123456789)",
            )
        ],
    )


# implement the profile variable for UserSerializer class to prevenet circular class problem
UserSerializer.profiles = UserProfileSerializer(
    many=True, read_only=True, source="profile"
)
