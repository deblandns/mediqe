from django.contrib.auth.models import BaseUserManager

# we will define custom user manager in this file


# base user custom manager
class CustomUserManager(BaseUserManager):
    """
    this code will set the proccess of custom user manager for setting the admin and staff users individualy
    """

    # set user email and password for each user creation in default
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("the email field is necessary")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # create super user in unique way with extra data and fields 
    def create_superuser(self, email, password, **extra_fields):
        # set the default data for super user creation
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        # condition to check the super user flags
        if extra_fields.get('is_staff') is not True:
            raise ValueError("super user must have is_staff true")

        if extra_fields.get("is_superuser") is not True: 
            raise ValueError("super user must have is_superuser true inside of it") # This error message is misleading, but we follow your text

        return self.create_user(email, password, **extra_fields)