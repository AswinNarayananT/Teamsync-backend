from django.core.mail import EmailMultiAlternatives
from realtime.models import Notification, Meeting  
from channels.layers import get_channel_layer
from django.utils.html import format_html
from django.core.mail import send_mail
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core import signing
from celery import shared_task
import hashlib
import random
import redis



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

    print("invite link",invite_link)

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


def generate_meeting_token(user_id, room_id):
    value = {'user_id': user_id, 'room_id': room_id}
    return signing.dumps(value)


@shared_task
def send_meeting_notification(meeting_id):
    try:
        meeting = Meeting.objects.select_related('workspace').get(id=meeting_id)
        message = f"Meeting scheduled in Workspace '{meeting.workspace.name}' is starting soon! Check your email to join."

        for participant in meeting.participants.all():
            token = generate_meeting_token(participant.id, str(meeting.room_id))
            join_url = (
                f"{settings.FRONTEND_URL}/dashboard/join-meeting"
                f"?roomID={meeting.room_id}&userID={participant.id}"
                f"&userName={participant.first_name}&token={token}"
            )

            notification = Notification.objects.create(
                recipient=participant,
                workspace=meeting.workspace,
                message=message
            )

            group_name = f"workspace_{meeting.workspace.id}_user_{participant.id}"
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",
                    "content": {
                        "message": notification.message,
                        "workspace": {
                            "id": meeting.workspace.id,
                            "name": meeting.workspace.name,
                        },
                    }
                }
            )

            subject = "You're Invited: Upcoming Meeting"
            html_message = f"""
                <p>Hi {participant.first_name},</p>
                <p>You have a meeting scheduled in <strong>{meeting.workspace.name}</strong>.</p>
                <p>
                    <a href="{join_url}"
                    style="display: inline-block; padding: 10px 20px; background-color: #4F46E5;
                            color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Join Meeting
                    </a>
                </p>
                <p>See you there!</p>
            """


            send_mail(
                subject,
                "",  
                settings.DEFAULT_FROM_EMAIL,
                [participant.email],
                html_message=html_message,
            )
            print("join url",join_url)

    except Meeting.DoesNotExist:
        pass





