from rest_framework import generics, permissions
from .models import Workspace, WorkspaceMember
from rest_framework.response import Response
from .serializers import WorkspaceSerializer
from django.utils.timezone import now
from adminpanel.models import Plan
from rest_framework import status
from django.conf import settings
from datetime import timedelta
import stripe

# Create your views here.


class UserWorkspacesView(generics.ListAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        member_workspaces = Workspace.objects.filter(members__user=user)

        return member_workspaces.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        for workspace in data:
            try:
                member = WorkspaceMember.objects.get(user=request.user, workspace_id=workspace["id"])
                workspace["role"] = member.role
            except WorkspaceMember.DoesNotExist:
                workspace["role"] = None

        return Response(data, status=200)
    


stripe.api_key = settings.STRIPE_SECRET_KEY

class WorkspaceCreateView(generics.CreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        if Workspace.objects.filter(owner=user).exists():
            raise ValueError("User already owns a workspace")

        plan_id = data.get("plan_id")
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            raise ValueError("Invalid Plan ID")

        if not serializer.is_valid():
            raise ValueError(serializer.errors)

        plan_expiry = now() + timedelta(days=plan.duration_days)

        workspace = serializer.save(
            owner=user,
            plan=plan,
            plan_expiry=plan_expiry,
            is_active=True,
        )

        WorkspaceMember.objects.create(user=user, workspace=workspace, role="owner")

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="subscription",
                customer_email=user.email,
                line_items=[
                    {
                        "price": plan.stripe_price_id,
                        "quantity": 1,
                    }
                ],
                success_url=f"{settings.FRONTEND_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/create-workspace",
                metadata={"workspace_id": workspace.id, "user_id": user.id},
            )
        except stripe.error.StripeError as e:
            workspace.delete() 
            raise ValueError(f"Stripe error: {str(e)}")

        return checkout_session

    def create(self, request, *args, **kwargs):
        try:
            checkout_session = self.perform_create(self.get_serializer(data=request.data))
            return Response({"message": "Workspace created successfully", "session_id": checkout_session.id, "redirect_url": checkout_session.url}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Workspace, WorkspaceInvitation
import uuid
from django.core.mail import EmailMultiAlternatives
from django.utils.html import format_html

class SendInvitesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        workspace_id = request.data.get("workspace_id")
        print(workspace_id)
        invites = request.data.get("invites", [])
        
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=user)
            print(workspace)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)
        
        # sent_invites = []
        for invite in invites:
            email = invite.get("email")
            full_name = invite.get("fullName")
            role = invite.get("role")
            
            if not email or not role:
                continue
            
            token = uuid.uuid4()
            invitation, created = WorkspaceInvitation.objects.update_or_create(
                email=email,
                workspace=workspace,
                defaults={"role": role, "token": token,"invited_by":user}
            )
            # sent_invites.append(invitation)
            
            invite_link = f"{settings.FRONTEND_URL}/join-workspace/{token}"


            # Create an HTML email with a centered button
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
                full_name,
                workspace.name,
                role,
                invite_link
            )

            email = EmailMultiAlternatives(
                subject="Workspace Invitation",
                body=f"Hello {full_name},\n\nYou have been invited to join '{workspace.name}' as a {role}.\nClick the link to accept: {invite_link}",
                from_email="no-reply@yourapp.com",
                to=[email],
            )
            email.attach_alternative(html_content, "text/html")  
            email.send()

        
        return Response({"message": "Invitations sent successfully!"}, status=status.HTTP_201_CREATED)



from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import WorkspaceInvitation, Workspace

class AcceptInviteView(APIView):
    def post(self, request):
        token = request.data.get("token")
        print(token)
        user = request.user

        try:
            invitation = WorkspaceInvitation.objects.get(token=token, email=user.email)
            if invitation.accepted:
                return Response({"error": "Invitation already used"}, status=status.HTTP_400_BAD_REQUEST)

            WorkspaceMember.objects.create(
                workspace=invitation.workspace,
                user=user,
                role=invitation.role  
            )

            invitation.accepted = True
            invitation.save()

            return Response({"message": "Successfully joined the workspace!"}, status=status.HTTP_200_OK)

        except WorkspaceInvitation.DoesNotExist:
            return Response({"error": "Invalid or expired invitation"}, status=status.HTTP_400_BAD_REQUEST)
