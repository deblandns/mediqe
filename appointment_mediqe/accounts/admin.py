from django.contrib import admin
from .models import User, UserProfile

# Register your models here.
@admin.register(User)
class UserCustomModelAdmin(admin.ModelAdmin):
    pass

@admin.register(UserProfile)
class UserProfileCustomAdmin(admin.ModelAdmin):
    pass