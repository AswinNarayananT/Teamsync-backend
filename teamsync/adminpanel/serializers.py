from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    stripe_product_id = serializers.CharField(read_only=True)
    stripe_price_id = serializers.CharField(read_only=True)

    class Meta:
        model = Plan
        fields = "__all__"
