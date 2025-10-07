import random
from django.contrib.auth.hashers import make_password


# function to generate otp
def otp_generator():
    try:
        otp = str(random.randint(100000, 999999))
        print(otp)
        return make_password(otp)
    except Exception as e:
        return None