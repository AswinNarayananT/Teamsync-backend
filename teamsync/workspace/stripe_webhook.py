from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.utils.timezone import now
from datetime import datetime
import stripe
from teamsync import settings
from accounts.models import Accounts
from adminpanel.models import Plan
from workspace.models import Workspace, WorkspaceMember
import traceback

@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print("it started")
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)

        event_type = event.get("type")
        data_object = event["data"]["object"]
        print("event type is",event_type)

        if event_type == "checkout.session.completed":
            return self.handle_checkout_completed(data_object)

        elif event_type == "customer.subscription.deleted":
            return self.handle_subscription_deleted(data_object)

        return HttpResponse(status=200)

    def handle_checkout_completed(self, session):
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        metadata = session.get("metadata", {})

        action = metadata.get("action")

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
            price_id = subscription["items"]["data"][0]["price"]["id"]
            plan = Plan.objects.filter(stripe_price_id=price_id).first()

            if action == "create":
                print("createing")
                user_id = metadata.get("user_id")
                workspace_name = metadata.get("workspace_name")
                workspace_type = metadata.get("workspace_type", "individual")
                work_type = metadata.get("work_type", "software_development")
                description = metadata.get("description", "")

                print("fetching user")
                user = Accounts.objects.get(id=user_id)

                workspace = Workspace.objects.create(
                    name=workspace_name,
                    owner=user,
                    workspace_type=workspace_type,
                    work_type=work_type,
                    description=description,
                    plan=plan,
                    plan_expiry=current_period_end,
                    is_active=True,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                )

                WorkspaceMember.objects.create(user=user, workspace=workspace, role="owner")

            elif action == "update":
                workspace_id = metadata.get("workspace_id")
                workspace = Workspace.objects.filter(id=workspace_id).first()

                if workspace and plan:
                    workspace.plan = plan
                    workspace.plan_expiry = current_period_end
                    workspace.stripe_subscription_id = subscription_id
                    workspace.stripe_customer_id = customer_id
                    workspace.is_active = True
                    workspace.save()

        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()
            return HttpResponse(status=400)

        return HttpResponse(status=200)

    def handle_subscription_deleted(self, subscription):
        sub_id = subscription.get("id")
        workspace = Workspace.objects.filter(stripe_subscription_id=sub_id).first()

        if workspace:
            workspace.deactivate_workspace()

        return HttpResponse(status=200)
