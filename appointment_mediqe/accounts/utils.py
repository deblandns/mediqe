import random
from django.contrib.auth.hashers import make_password


# function to generate otp
def otp_generator():
    try:
        return make_password(str(random.randint(100000, 999999)))
    except Exception as e:
        return None
    


# function to store the cache data inside the redis database
