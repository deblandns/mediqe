from rest_framework import serializers
from ..models import User, UserProfile


# custom user serializer to serilize data of user
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        # read only fields
        read_only_fields = ("group", "permissions")
        # Ensure password is write-only
        extra_kwargs = {
            "password": {
                "write_only": True,
                "style": {"input_type": "password", "placeholder": "Password"},
            }
        }

    # set user password in a hashed way correctly when creating new user
    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    # set password of user when updating the user
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attribute, values in validated_data.items():
            setattr(instance, attribute, values)
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
        print(validated_data)
        # This will now correctly receive the 'user' data because of the field definition above
        user_data = validated_data.pop("user")
        password = user_data.pop("password", None)
        user = User(**user_data)
        if password:
            user.set_password(password)
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


# implement the profile variable for UserSerializer class to prevenet circular class problem
UserSerializer.profiles = UserProfileSerializer(
    many=True, read_only=True, source="profile"
)
