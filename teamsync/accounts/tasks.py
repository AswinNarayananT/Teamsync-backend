import hashlib
import redis
import random
from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
from accounts.models import Accounts


redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

@shared_task
def send_otp_email(user_id, email):

    otp = str(random.randint(100000, 999999))

    otp_hash = hashlib.sha256(otp.encode()).hexdigest()

    redis_client.setex(f"otp:{user_id}", 120, otp_hash)

    subject = "Your OTP for Team Sync"
    message = f"Your OTP code is: {otp}. It is valid for 2 minutes."
    send_mail(subject, message, "noreply@teamsync.com", [email])

    return f"OTP {otp} sent to {email}"
