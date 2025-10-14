from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

# warning the test inputs are change from the version before may the authentication doesn`t work using this test case

# --- Mock Data ---

USER_1_DATA = {
    "email": "u1@test.com",
    "password": "pass1",
    "username": "userone",
    "role": "Patient",
    "gender": "Male",
}

NESTED_PROFILE_DATA = {
    "insurance_number": "INS999",
    "blood_types": "O-",
    "chronic_conditions": "None",
    "user": {
        "email": "d2@test.com",
        "password": "docpass",
        "username": "doctortwo",
        "role": "Doctor",
        "gender": "Female",
        "years_of_experiences": 5,
    },
}


class UserViewTests(APITestCase):
    """Tests the /users/ API endpoint."""

    def setUp(self):
        # Create a user directly for testing list/retrieve
        self.user_instance = User.objects.create_user(**USER_1_DATA)
        self.list_url = reverse("users-list")  # 'users' is the basename from urls.py

    def test_list_users_success(self):
        """Ensure users list is accessible."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "u1@test.com")

    def test_create_user_success(self):
        """Ensure a new user can be created via POST."""
        new_user_data = {
            "email": "new@test.com",
            "password": "newpassword123",
            "role": "Patient",
            "gender": "Other",
        }
        response = self.client.post(self.list_url, new_user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify user was created in the database and password is hashed
        user = User.objects.get(email="new@test.com")
        self.assertTrue(user.check_password("newpassword123"))
        self.assertEqual(user.role, "Patient")


class UserProfileViewTests(APITestCase):
    """Tests the /profiles/ API endpoint, focusing on nested writes."""

    def setUp(self):
        self.list_url = reverse(
            "profiles-list"
        )  # 'profiles' is the basename from urls.py
        # Create a pre-existing user and profile for updates/retrieval
        user = User.objects.create_user(
            email="existing@user.com", password="oldpass", role="Doctor", gender="Male"
        )
        self.profile_instance = UserProfile.objects.create(
            user=user,
            insurance_number="INS999",
            blood_types="O-",
            chronic_conditions="None",
        )
        self.detail_url = reverse(
            "profiles-detail", kwargs={"pk": self.profile_instance.pk}
        )

    def test_nested_create_profile_and_user_success(self):
        """
        Crucial test: POST to /profiles/ with nested data must create both User and Profile.
        """
        response = self.client.post(self.list_url, NESTED_PROFILE_DATA, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 1. Verify UserProfile was created
        profile_id = response.data["id"]
        self.assertTrue(UserProfile.objects.filter(pk=profile_id).exists())
        self.assertEqual(response.data["insurance_number"], "INS999")

        # 2. Verify User was created and linked
        user = User.objects.get(email="d2@test.com")
        self.assertTrue(user.check_password("docpass"))
        self.assertEqual(user.role, "Doctor")

        # 3. Verify the nested structure of the response
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "d2@test.com")

    def test_update_profile_and_nested_user_fields(self):
        """
        Ensure PATCH to /profiles/{pk}/ can update both profile fields and nested user fields.
        """
        update_data = {
            "speciality": "Pediatrics",
            "user": {"first_name": "Jane", "password": "newpassword456"},
        }

        response = self.client.patch(self.detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Reload objects from DB
        self.profile_instance.refresh_from_db()
        user = self.profile_instance.user

        # Check Profile update
        self.assertEqual(self.profile_instance.speciality, "Pediatrics")

        # Check User updates
        self.assertEqual(user.first_name, "Jane")
        self.assertTrue(user.check_password("newpassword456"))
