from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    stripe_product_id = serializers.CharField(read_only=True)
    stripe_price_id = serializers.CharField(read_only=True)

    class Meta:
        model = Plan
        fields = "__all__"

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
