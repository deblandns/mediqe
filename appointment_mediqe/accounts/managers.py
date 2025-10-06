from django.contrib.auth.models import BaseUserManager

# we will define custom user manager in this file


# base user custom manager
class CustomUserManager(BaseUserManager):
    """
    this code will set the proccess of custom user manager for setting the admin and staff users individualy
    """

    # set user email and password for each user creation in default
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("the phone field is necessary")
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password() # for otp codes
        user.save(using=self._db)
        return user

    # overwrite the createsuper user with desire data
    def create_superuser(self, phone, password=None, **extra_fields):
        # set default flags for superuser
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(phone, password, **extra_fields)