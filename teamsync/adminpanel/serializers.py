from rest_framework import serializers
from .models import Plan
from workspace.models import Workspace
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY 

class PlanSerializer(serializers.ModelSerializer):
    stripe_product_id = serializers.CharField(read_only=True)
    stripe_price_id = serializers.CharField(read_only=True)

    class Meta:
        model = Plan
        fields = "__all__"


class WorkspaceSerializer(serializers.ModelSerializer):
    plan_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    formatted_plan_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'id', 'name', 'description', 'created_at',
            'is_active', 'is_blocked_by_admin', 'formatted_plan_expiry',
            'plan_name', 'member_count', 'subscription_status',
        ]

    def get_plan_name(self, obj):
        return obj.plan.name if obj.plan else "No Plan"

    def get_member_count(self, obj):
        return obj.members.count()

    def get_subscription_status(self, obj):
        if not obj.stripe_subscription_id:
            return "no_subscription"
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            subscription = stripe.Subscription.retrieve(obj.stripe_subscription_id)
            return subscription.status
        except stripe.error.InvalidRequestError:
            return "invalid_subscription"
        except Exception:
            return "error"

    def get_formatted_plan_expiry(self, obj):
        if obj.plan_expiry:
            print( obj.plan_expiry.strftime("%B %d, %Y"))
            return obj.plan_expiry.strftime("%B %d, %Y") 
        return None

class PlanAdminSerializer(serializers.ModelSerializer):
    active_subscriptions = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    weekly_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    yearly_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    active_workspaces = serializers.IntegerField()
    blocked_workspaces = serializers.IntegerField()
    expired_workspaces = serializers.IntegerField()

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'price', 'duration_days',
            'active_subscriptions', 'total_revenue', 'monthly_revenue', 'weekly_revenue', 'yearly_revenue',
            'active_workspaces', 'blocked_workspaces', 'expired_workspaces',
        ]
