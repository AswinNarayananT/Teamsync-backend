from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Workspace, WorkspaceMember
from django.utils.timezone import now
from .serializers import WorkspaceSerializer

# Create your views here.


class UserWorkspacesView(generics.ListAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Fetch workspaces where the user is a member
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
    

import stripe
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from .models import Workspace, WorkspaceMember
from .serializers import WorkspaceSerializer
from adminpanel.models import Plan

stripe.api_key = settings.STRIPE_SECRET_KEY

class WorkspaceCreateView(generics.CreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        # ✅ Ensure user doesn't already own a workspace
        if Workspace.objects.filter(owner=user).exists():
            raise ValueError("User already owns a workspace")

        # ✅ Fetch the selected plan
        plan_id = data.get("plan_id")
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            raise ValueError("Invalid Plan ID")

        # ✅ Validate serializer
        if not serializer.is_valid():
            raise ValueError(serializer.errors)

        # ✅ Set workspace expiry based on plan duration
        plan_expiry = now() + timedelta(days=plan.duration_days)

        # ✅ Create the workspace
        workspace = serializer.save(
            owner=user,
            plan=plan,
            plan_expiry=plan_expiry,
            is_active=True,
        )

        # ✅ Add the owner to WorkspaceMember as "Owner"
        WorkspaceMember.objects.create(user=user, workspace=workspace, role="owner")

        # ✅ Create Stripe Checkout Session
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
            workspace.delete()  # ❌ Rollback if Stripe fails
            raise ValueError(f"Stripe error: {str(e)}")

        return checkout_session

    def create(self, request, *args, **kwargs):
        try:
            checkout_session = self.perform_create(self.get_serializer(data=request.data))
            return Response({"message": "Workspace created successfully", "session_id": checkout_session.id, "redirect_url": checkout_session.url}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


