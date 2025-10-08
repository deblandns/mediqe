from celery import shared_task

@shared_task
def send_otp_code(user_phone_number, otp):
    # Logic to send OTP code to the user's phone number
    print(user_phone_number, otp)