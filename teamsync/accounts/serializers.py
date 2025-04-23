from .models import Accounts, OTPVerification
from django.utils.timezone import now, timedelta
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from rest_framework import serializers
import hashlib
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from accounts.tasks import send_otp_email
import redis
from django.core.exceptions import ValidationError
from rest_framework import serializers
from accounts.models import Accounts

redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)



User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accounts
        fields = ["email", "first_name", "last_name", "phone_number", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        if self.context.get("resend_otp"):
            user = Accounts.objects.get(email=validated_data["email"])
        else:
            password = validated_data.pop("password")
            user = Accounts.objects.create(**validated_data)
            user.set_password(password)
            user.is_active = False
            user.save()

        send_otp_email.delay(user.id, user.email)
        return user



class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        otp = data.get("otp")

        try:
            user = Accounts.objects.get(email=email)
        except Accounts.DoesNotExist:
            raise serializers.ValidationError("Invalid email or OTP.")

        otp_key = f"otp:{user.id}"
        stored_otp_hash = redis_client.get(otp_key)

        if not stored_otp_hash:
            raise serializers.ValidationError("OTP has expired or is invalid.")

        if stored_otp_hash != hashlib.sha256(otp.encode()).hexdigest():
            raise serializers.ValidationError("Invalid OTP.")

        user.otp_verified = True
        user.is_active = True  
        user.save()

        redis_client.delete(otp_key)

        return {"message": "OTP verified successfully", "user_id": user.id}


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        email = data.get("email")
        print(email)
        try:
            user = Accounts.objects.get(email=email)
        except Accounts.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        send_otp_email.delay(user.id, user.email)

        return {"message": "OTP has been resent to your email."}


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email is None or password is None: 
            raise serializers.ValidationError("Invalid email or password.")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if user.google_verified and not user.password:
            raise serializers.ValidationError("Use Google Sign-In for this account.")

        user = authenticate(email=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        

        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")
        
        if user.is_blocked:
            raise serializers.ValidationError("Account is blocked.")

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number":user.phone_number,
                "profile_picture":user.profile_picture,
                "is_superuser":user.is_superuser
            },
            "access_token": str(access),  
            "refresh_token": str(refresh),
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accounts
        exclude = ["password"]     


class UserDetailUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accounts
        fields = ['first_name', 'last_name', 'phone_number'] 


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not Accounts.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data