import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Permission, Group
from .managers import CustomUserManager

# extended user class to extend user data in user model of django
class User(AbstractBaseUser):
    # important fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False, blank=False, editable=False)
    username = models.CharField(max_length=120, unique=True, null=True, blank=True, verbose_name='user name')
    email = models.EmailField(max_length=300, unique=True, null=False, blank=False, verbose_name="email")
    password = models.CharField(max_length=600, null=False, blank=False, verbose_name="password") # will be hashed password

    # standard fields
    first_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="first name")
    last_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="last name")

    # custom fields for Role
    ROLES = [
        ("Admin", "Admin"),
        ("Doctor", "Doctor"),
        ("Patient", "Patient"),
        ("Nurse", "Nurse"),
        ("Receptionist", "Receptionist"),
    ]

    # custom fields for Role
    GENDERS = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    role = models.CharField(max_length=25, choices=ROLES, default="Patient", null=False, blank=False, verbose_name="user role")
    gender = models.CharField(max_length=20, null=False, blank=False, choices=GENDERS, verbose_name="user gender")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="date of birth")
    phone = models.CharField(max_length=15, null=False, blank=False, verbose_name="phone number")
    address = models.CharField(max_length=150, null=True, blank=True, verbose_name="user address")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True, verbose_name="user image")
    
    # Permission/Status Fields
    is_active = models.BooleanField(default=True, verbose_name="is user active")
    is_staff = models.BooleanField(default=False, verbose_name="is user staff")
    is_verified = models.BooleanField(default=False, verbose_name="is user verified or not")

    # Date Fields
    created_at = models.DateTimeField(auto_now_add=True)

    # extra informations 
    extra_info = models.JSONField(null=True, blank=True, verbose_name="extra fields and data")

    objects = CustomUserManager()
    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = [] # these are fields that are required 

    def __str__(self):
        return f"{self.email}"


class UserProfile(models.Model):
    """
    Model to store supplementary, optional information for a User.
    This implements the 'User "1" -- "0..1" UserProfile' relationship.
    """

    BLOOD_TYPES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile') # connected as multiple to one filed to user model
    insurance_number = models.CharField(null=True, blank=True, max_length=200, verbose_name="Insurance Number")
    insurance_company = models.CharField(null=True, blank=True, max_length=50, verbose_name="insurance company")
    blood_types = models.CharField(max_length=10, choices=BLOOD_TYPES, null=False, blank=False, verbose_name="blood type")
    chronic_conditions = models.TextField(null=True, blank=True, verbose_name="chronic conditions")
    license_number = models.CharField(max_length=80, null=True, blank=True, verbose_name="license number")
    speciality = models.CharField(max_length=100, null=True, blank=True, verbose_name="Speciality")
    bio = models.TextField(null=True, blank=True, verbose_name="biogeraphy")
    years_of_experiences = models.IntegerField(null=True, blank=True, verbose_name="yeasr of experiences")
    rating = models.FloatField(null=True, blank=True, verbose_name="raing of profile")
    verified = models.BooleanField(default=False, verbose_name="verified")

    def __str__(self):
        return f"Profile for {self.user.email}"