from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import stripe
from .models import Plan
from .serializers import PlanSerializer
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from workspace.serializers import WorkspaceSerializer
from workspace.models import Workspace
from django.utils.timezone import now
from django.db.models import Count, Sum, Q, F
import datetime 
import stripe
from rest_framework.permissions import IsAdminUser






stripe.api_key = settings.STRIPE_SECRET_KEY 


class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        data = self.request.data

        try:
            duration = int(data.get("duration_days", 30))
        except ValueError:
            return Response({"error": "Invalid duration_days"}, status=status.HTTP_400_BAD_REQUEST)

        interval = "month"
        interval_count = 1
        if duration == 90:
            interval_count = 3
        elif duration == 180:
            interval_count = 6
        elif duration == 365:
            interval = "year"

        try:
            stripe_product = stripe.Product.create(
                name=data["name"],
                description=data.get("description", ""),
            )

            stripe_price = stripe.Price.create(
                unit_amount=int(float(data["price"]) * 100),  
                currency="usd",
                recurring={"interval": interval, "interval_count": interval_count},
                product=stripe_product.id,
            )

            serializer.save(
                stripe_product_id=stripe_product.id,
                stripe_price_id=stripe_price.id
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "DELETE"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        instance = self.get_object()
        data = self.request.data

        duration = int(data.get("duration_days", 30))

        if duration < 365:
            interval = "month"
            interval_count = max(1, duration // 30)  
        else:
            interval = "year"
            interval_count = min(3, duration // 365)

            stripe.Product.modify(instance.stripe_product_id, name=data.get("name", instance.name))

        stripe.Product.modify(
            instance.stripe_product_id,
            name=data["name"],
            description=data.get("description", "")
        )

        stripe_price = stripe.Price.create(
            unit_amount=int(float(data["price"]) * 100), 
            currency="usd",
            recurring={"interval": interval, "interval_count": interval_count},
            product=instance.stripe_product_id
        )

        serializer.save(
            stripe_price_id=stripe_price.id
        )


class PlanDeleteView(generics.DestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        plan = self.get_object()
        
        try:
            if plan.stripe_product_id:
                stripe.Product.modify(plan.stripe_product_id, active=False)  

            if plan.stripe_price_id:
                stripe.Price.modify(plan.stripe_price_id, active=False) 

        except stripe.error.StripeError as e:
            return Response({"error": "Failed to delete plan from Stripe"}, status=status.HTTP_400_BAD_REQUEST)

        response = super().delete(request, *args, **kwargs)
        return Response({"message": "Plan deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    

class AdminWorkspaceListView(generics.ListAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAdminUser]




class PlanAdminStatsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = now()
        data = []

        plans = Plan.objects.filter(is_active=True)

        for plan in plans:
            workspaces = Workspace.objects.filter(plan=plan)
            active_workspaces = workspaces.filter(
                is_active=True, is_blocked_by_admin=False, plan_expiry__gt=today
            ).count()
            blocked_workspaces = workspaces.filter(is_blocked_by_admin=True).count()
            expired_workspaces = workspaces.filter(
                Q(plan_expiry__lte=today) | Q(is_active=False, is_blocked_by_admin=False)
            ).count()

            stripe_subscriptions = stripe.Subscription.list(limit=100, status='all')

            plan_subscriptions = [
                sub for sub in stripe_subscriptions.auto_paging_iter()
                if any(item.price.id == plan.stripe_price_id for item in sub.items.data)
            ]

            active_sub_count = sum(1 for sub in plan_subscriptions if sub.status == "active")
            cancelled_sub_count = sum(1 for sub in plan_subscriptions if sub.status in ["canceled", "incomplete_expired", "unpaid"])

            total_revenue_cents = 0
            monthly_revenue_cents = 0
            weekly_revenue_cents = 0
            yearly_revenue_cents = 0

            for sub in plan_subscriptions:
                latest_invoice = getattr(sub, 'latest_invoice', None)
                if not latest_invoice:
                    continue
                invoice_obj = stripe.Invoice.retrieve(latest_invoice)
                payment_intent = getattr(invoice_obj, 'payment_intent', None)
                if not payment_intent:
                    continue
                pi_obj = stripe.PaymentIntent.retrieve(payment_intent)
                if pi_obj.status == 'succeeded' and pi_obj.amount_received:
                    amount = pi_obj.amount_received
                    total_revenue_cents += amount
                    created_dt = datetime.datetime.fromtimestamp(pi_obj.created)
                    delta = today - created_dt.replace(tzinfo=None)
                    if delta.days <= 7:
                        weekly_revenue_cents += amount
                    if delta.days <= 30:
                        monthly_revenue_cents += amount
                    if delta.days <= 365:
                        yearly_revenue_cents += amount

            def cents_to_dollars(cents):
                return round(cents / 100, 2)

            data.append({
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'price': plan.price,
                'duration_days': plan.duration_days,

                'active_workspaces': active_workspaces,
                'blocked_workspaces': blocked_workspaces,
                'expired_workspaces': expired_workspaces,

                'active_subscriptions': active_sub_count,
                'cancelled_subscriptions': cancelled_sub_count,

                'total_revenue': cents_to_dollars(total_revenue_cents),
                'monthly_revenue': cents_to_dollars(monthly_revenue_cents),
                'weekly_revenue': cents_to_dollars(weekly_revenue_cents),
                'yearly_revenue': cents_to_dollars(yearly_revenue_cents),
            })

        return Response(data)
