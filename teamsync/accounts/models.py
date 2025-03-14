from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.timezone import now, timedelta
from django.db import models
import hashlib
import random


class AccountsManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True) 
        return self.create_user(email, password, **extra_fields)

class Accounts(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True) 
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True) 

    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False) 
    is_superuser = models.BooleanField(default=False)  
    last_login = models.DateTimeField(auto_now=True)  
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = AccountsManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"] 

    def __str__(self):
        return self.email


class OTPVerification(models.Model):
    user = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    otp_hash = models.CharField(max_length=128)  
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.IntegerField(default=0) 

    def is_valid(self, otp):
        if now() > self.created_at + timedelta(minutes=2):  
            return False  
        return self.otp_hash == hashlib.sha256(otp.encode()).hexdigest()

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))