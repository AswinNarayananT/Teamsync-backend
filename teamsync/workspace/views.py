from rest_framework import generics, permissions,status
from .models import Workspace, WorkspaceMember,WorkspaceInvitation, CustomRole
from rest_framework.response import Response
from .serializers import WorkspaceSerializer, WorkspaceMemberSerializer, CustomRoleSerializer
from adminpanel.models import Plan
from rest_framework import status
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.tasks import send_invitation_email
from django.shortcuts import get_object_or_404
import stripe
import uuid
from project.permissions import HasWorkspacePermission

# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY



class UserWorkspacesView(generics.ListAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        member_workspaces = Workspace.objects.filter(members__user=user).order_by("-members__joined_at").distinct()

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

    def perform_create(self, validated_data):
        user = self.request.user
        data = self.request.data

        if Workspace.objects.filter(owner=user).exists():
            raise ValueError("User already owns a workspace")

        plan_id = data.get("plan_id")
        workspace_name = data.get("name")
        workspace_type = data.get("workspace_type", "individual")
        work_type = data.get("work_type", "software_development")
        description = data.get("description", "")

        if not workspace_name or not plan_id:
            raise ValueError("Missing required fields")

        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            raise ValueError("Invalid Plan ID")

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
                metadata={
                    "action": "create",
                    "user_id": user.id,
                    "plan_id": plan.id,
                    "workspace_name": workspace_name,
                    "workspace_type": workspace_type,
                    "work_type": work_type,
                    "description": description,
                },
            )
            return checkout_session

        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            checkout_session = self.perform_create(serializer.validated_data)
            return Response({
                "message": "Stripe session created",
                "session_id": checkout_session.id,
                "redirect_url": checkout_session.url,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





class SendInvitesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        workspace_id = request.data.get("workspace_id")
        invites = request.data.get("invites", [])
        
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        if workspace.owner != user:
            return Response({"error": "You are not authorized to invite members to this workspace"}, status=status.HTTP_403_FORBIDDEN)
        
        for invite in invites:
            email = invite.get("email")
            full_name = invite.get("fullName")
            role = invite.get("role")
            
            if not email or not role:
                continue

            existing_member = WorkspaceMember.objects.filter(user__email=email, workspace=workspace).exists()
            if existing_member:
                continue

            token = str(uuid.uuid4())
            WorkspaceInvitation.objects.update_or_create(
                email=email,
                workspace=workspace,
                defaults={"role": role, "token": token, "invited_by": user}
            )

            send_invitation_email.delay(email, full_name, role, workspace.name, token)

        return Response({"message": "Invitations sent successfully!"}, status=status.HTTP_201_CREATED)




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
                role=invitation.role.lower()  
            )

            invitation.accepted = True
            invitation.save()

            return Response({"message": "Successfully joined the workspace!"}, status=status.HTTP_200_OK)

        except WorkspaceInvitation.DoesNotExist:
            return Response({"error": "Invalid or expired invitation"}, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceMembersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workspace_id):
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=404)

        members = WorkspaceMember.objects.filter(workspace=workspace).select_related("user")
        serializer = WorkspaceMemberSerializer(members, many=True)
        return Response({"members": serializer.data})
    


class WorkspaceSubscriptionUpdateView(APIView):

    def get(self, request, *args, **kwargs):
        print("🔥 GET METHOD CALLED")
        return Response({"message": "GET method works, view is accessible"}, status=200)

    def post(self, request, *args, **kwargs):
        print("🔥 POST METHOD CALLED - View is working!")

        user = request.user
        workspace_id = request.data.get("workspace_id")
        plan_id = request.data.get("plan_id")

        if not workspace_id or not plan_id:
            print("❌ Missing workspace_id or plan_id")
            return Response({"error": "workspace_id and plan_id are required"}, status=400)

        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=user)
        except Workspace.DoesNotExist:
            print("❌ Workspace not found or user not owner")
            return Response({"error": "Workspace not found or permission denied"}, status=404)

        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            print("❌ Invalid plan ID")
            return Response({"error": "Invalid Plan ID"}, status=400)

        try:
            print("✅ Creating Stripe checkout session...")
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
                cancel_url=f"{settings.FRONTEND_URL}/subscription/update",
                metadata={
                    "action": "update",
                    "workspace_id": workspace.id,
                    "user_id": user.id,
                    "plan_id": plan.id,
                },
            )

            print("✅ Stripe session created:", checkout_session.id)

            return Response({
                "message": "Stripe session created for subscription update",
                "session_id": checkout_session.id,
                "redirect_url": checkout_session.url,
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            print("❌ Stripe error:", e)
            return Response({"error": f"Stripe error: {str(e)}"}, status=400)
        



class StripeSubscriptionDetailView(APIView):
    def get(self, request, subscription_id):
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            item = subscription["items"]["data"][0]
            price = stripe.Price.retrieve(item["price"]["id"])
            product = stripe.Product.retrieve(price["product"])

            return Response({
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "price": {
                    "id": price.id,
                    "unit_amount": price.unit_amount,
                    "interval": price.recurring["interval"],
                    "interval_count": price.recurring["interval_count"],
                    "currency": price.currency
                },
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description
                }
            })

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class WorkspaceStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        try:
            workspace = Workspace.objects.get(id=workspace_id)

            is_member = WorkspaceMember.objects.filter(
                workspace=workspace, user=request.user
            ).exists()

            if not is_member:
                return Response(
                    {"detail": "You do not have permission to access this workspace."},
                    status=status.HTTP_403_FORBIDDEN
                )

            return Response({
                "id": str(workspace.id),
                "is_active": workspace.is_active,
                "is_blocked_by_admin": workspace.is_blocked_by_admin, 
            }, status=status.HTTP_200_OK)

        except Workspace.DoesNotExist:
            return Response(
                {"detail": "Workspace not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        subscription_id = request.data.get("subscription_id")
        if not subscription_id:
            return Response({"error": "Subscription ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workspace = get_object_or_404(Workspace, stripe_subscription_id=subscription_id)

            if workspace.owner != request.user:
                return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )

            return Response({"message": "Subscription will be canceled at period end."})
        except Exception as e:
            print(f"Stripe error: {e}")
            return Response({"error": "Failed to cancel subscription."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CreateCustomRoleView(APIView):
    permission_classes = [IsAuthenticated, HasWorkspacePermission]
    required_permissions = ["create_custom_role"]

    def post(self, request, workspace_id):
        role_name = request.data.get("name")
        permissions = request.data.get("permissions", [])

        if not role_name or not isinstance(permissions, list):
            return Response({"error": "Invalid input"}, status=400)

        role = CustomRole.objects.create(
            workspace=request.current_workspace,
            name=role_name,
            permissions=permissions
        )

        serialized = CustomRoleSerializer(role)
        return Response(serialized.data, status=201)
    


class CustomRoleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        # You can add check for workspace.owner == request.user if needed
        roles = CustomRole.objects.filter(workspace=workspace)
        serializer = CustomRoleSerializer(roles, many=True)
        return Response(serializer.data)

    def post(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        serializer = CustomRoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(workspace=workspace)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomRoleUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, workspace_id, role_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        role = get_object_or_404(CustomRole, id=role_id, workspace=workspace)
        serializer = CustomRoleSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, workspace_id, role_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        role = get_object_or_404(CustomRole, id=role_id, workspace=workspace)
        role.delete()
        return Response({"detail": "Role deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    

class RemoveUserFromWorkspaceView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    required_permissions = ["team_management"] 

    def delete(self, request, workspace_id, user_id):
        user = request.user

        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.id == int(user_id):
            return Response({"error": "You cannot remove yourself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = WorkspaceMember.objects.get(workspace=workspace, id=user_id)
            member.delete()
            return Response(
                {"message": "User removed from workspace.", "id": user_id},
                status=status.HTTP_200_OK
            )
        except WorkspaceMember.DoesNotExist:
            return Response({"error": "User is not a member of this workspace."}, status=status.HTTP_404_NOT_FOUND)