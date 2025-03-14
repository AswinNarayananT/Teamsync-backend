from .models import Accounts, OTPVerification
from django.utils.timezone import now, timedelta
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from rest_framework import serializers
import hashlib
import random


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model =Accounts
        fields = ["email","first_name","last_name","phone_number","password"]
        extra_kwargs = {"password":{"write_only":True}}

    def create(self, validated_data):

        password =validated_data.pop("password")
        user =Accounts.objects.create(password=password,**validated_data)
        user.is_active =False
        user.save()

        otp = OTPVerification.generate_otp()
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        OTPVerification.objects.filter(user=user).delete()
        OTPVerification.objects.create(user=user, otp_hash=otp_hash)
        print(f"OTP for {user.email}: {otp}")

        send_mail(
            subject="Your OTP for Team Sync",
            message=f"Your OTP code is: {otp}. It is valid for 2 minutes.",
            from_email="noreply@teamsync.com",
            recipient_list=[user.email],
        )

        return user   


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        otp = data.get("otp")

        try:
            user = Accounts.objects.get(email=email)
            otp_entry = OTPVerification.objects.filter(user=user).latest('created_at')
        except (Accounts.DoesNotExist, OTPVerification.DoesNotExist):
            raise serializers.ValidationError("Invalid email or OTP.")

        if not otp_entry.is_valid:
            raise serializers.ValidationError("OTP has expired.")

        if otp_entry.otp_hash != hashlib.sha256(otp.encode()).hexdigest():
            otp_entry.attempts += 1
            otp_entry.save()
            raise serializers.ValidationError("Invalid OTP.")

        otp_entry.delete()
        return {"message": "OTP verified successfully", "user_id": user.id}


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        email = data.get("email")
        try:
            user = Accounts.objects.get(email=email)
        except Accounts.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        OTPVerification.objects.filter(user=user).delete()  
        otp = OTPVerification.generate_otp()
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        OTPVerification.objects.create(user=user, otp_hash=otp_hash)

        send_mail(
            subject="Resend OTP for Team Sync",
            message=f"Your new OTP code is: {otp}. It is valid for 2 minutes.",
            from_email="noreply@teamsync.com",
            recipient_list=[user.email],
        )

        return {"message": "OTP has been resent to your email."}


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        user = authenticate(email=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")
        
        if user.is_blocked:
            raise serializers.ValidationError("Account is Blocked.")

        return {"message": "Login successful", "user_id": user.id}