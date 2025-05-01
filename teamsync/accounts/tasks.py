import hashlib
import redis
import random
from celery import shared_task
from django.core.mail import send_mail
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils.html import format_html
from django.conf import settings



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




@shared_task
def send_invitation_email(email, full_name, role, workspace_name, token):
    invite_link = f"{settings.FRONTEND_URL}/join-workspace/{token}"

    html_content = format_html(
        """
        <div style="text-align: center; font-family: Arial, sans-serif;">
            <h2>Hello {},</h2>
            <p>You have been invited to join <strong>{}</strong> as a <strong>{}</strong>.</p>
            <p>Click the button below to accept the invitation:</p>
            <a href="{}" style="
                display: inline-block;
                padding: 12px 20px;
                font-size: 16px;
                color: white;
                background-color: #007bff;
                text-decoration: none;
                border-radius: 5px;
            ">Accept Invitation</a>
        </div>
        """, 
        full_name, workspace_name, role, invite_link
    )

    email_obj = EmailMultiAlternatives(
        subject="Workspace Invitation",
        body=f"Hello {full_name},\n\nYou have been invited to join '{workspace_name}' as a {role}.\nClick the link to accept: {invite_link}",
        from_email="no-reply@yourapp.com",
        to=[email],
    )
    email_obj.attach_alternative(html_content, "text/html")
    email_obj.send()


@shared_task
def send_password_reset_email(email, reset_link):
    subject = "Password Reset"
    message = f"Reset your password using this link: {reset_link}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)