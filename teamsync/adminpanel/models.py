from django.db import models

# Create your models here.



class Plan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    stripe_product_id = models.CharField(max_length=100, unique=True) 
    stripe_price_id = models.CharField(max_length=100, unique=True) 
    duration_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
