from django.test import TestCase
from django.contrib.auth.hashers import check_password
from .models import User, UserProfile
from .v1.serializers import UserSerializer, UserProfileSerializer

# warning the test inputs are change from the version before may the authentication doesn`t work using this test case

# Mock data for testing
USER_DATA = {
    "email": "test@example.com",
    "password": "securepassword123",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "role": "Patient",
    "gender": "Male",
}

PROFILE_DATA = {
    "insurance_number": "INS123",
    "insurance_company": "HealthCorp",
    "blood_types": "A+",
    "chronic_conditions": "Asthma",
}


class UserSerializerTests(TestCase):
    """Tests for UserSerializer's create and update methods."""

    def test_create_user_hashes_password(self):
        """Ensure that creating a user hashes the password correctly."""
        serializer = UserSerializer(data=USER_DATA)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Check if the password is NOT stored as plain text
        self.assertNotEqual(user.password, USER_DATA["password"])

        # Check if the password is valid when checked against the plain text
        self.assertTrue(check_password(USER_DATA["password"], user.password))
        self.assertEqual(user.email, USER_DATA["email"])
        self.assertEqual(user.role, USER_DATA["role"])

    def test_update_user_updates_password(self):
        """Ensure that updating a user hashes the new password correctly."""
        # 1. Create a user first
        user = User.objects.create_user(**USER_DATA)
        original_password = user.password

        # 2. Define data for updating the password
        new_password = "newsecurepassword456"
        update_data = {
            "email": USER_DATA[
                "email"
            ],  # Email required for validation, though not changing
            "password": new_password,
            "first_name": "UpdatedName",  # Also test another field update
        }

        serializer = UserSerializer(instance=user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Check if password changed and is correctly hashed
        self.assertNotEqual(updated_user.password, original_password)
        self.assertTrue(check_password(new_password, updated_user.password))

        # Check if other field was updated
        self.assertEqual(updated_user.first_name, "UpdatedName")


class UserProfileSerializerTests(TestCase):
    """Tests for UserProfileSerializer's nested create and update methods."""

    def setUp(self):
        # Setup a combined payload for nested creation
        self.nested_payload = {
            **PROFILE_DATA,
            "user": {
                "email": "nested@test.com",
                "password": "nestedpassword",
                "username": "nesteduser",
                "gender": "Female",
                "role": "Doctor",
            },
        }

    def test_nested_create(self):
        """Ensure that User and UserProfile are created and linked correctly."""
        print(self.nested_payload)
        serializer = UserProfileSerializer(data=self.nested_payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        profile = serializer.save()

        # 1. Check if UserProfile was created with correct data
        self.assertIsInstance(profile, UserProfile)
        self.assertEqual(profile.insurance_number, PROFILE_DATA["insurance_number"])
        self.assertEqual(profile.user.email, "nested@test.com")

        # 2. Check if the User was created and linked
        user = profile.user
        self.assertIsInstance(user, User)
        self.assertEqual(user.role, "Doctor")

        # 3. Check if the password was hashed
        self.assertTrue(check_password("nestedpassword", user.password))

    def test_nested_update_both_user_and_profile(self):
        """Ensure that nested update can modify both User and UserProfile fields."""
        # 1. Create initial profile/user
        User.objects.create(**self.nested_payload["user"])
        user = User.objects.get(email="nested@test.com")
        profile = UserProfile.objects.create(user=user, **PROFILE_DATA)

        # Store original password hash for comparison
        original_hash = user.password

        # 2. Define update data
        update_data = {
            "insurance_company": "New HealthCo",
            "user": {
                "first_name": "Dr. Sarah",
                "password": "newpassword",  # New password to hash
            },
        }

        serializer = UserProfileSerializer(
            instance=profile, data=update_data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_profile = serializer.save()
        updated_user = updated_profile.user

        # Check Profile update
        self.assertEqual(updated_profile.insurance_company, "New HealthCo")

        # Check User update (first_name)
        self.assertEqual(updated_user.first_name, "Dr. Sarah")

        # Check User password update (CRITICAL)
        self.assertNotEqual(updated_user.password, original_hash)
        self.assertTrue(check_password("newpassword", updated_user.password))
