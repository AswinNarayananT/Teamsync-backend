from .serializers import UserRegisterSerializer,LoginSerializer,ResendOTPSerializer,OTPVerificationSerializer,UserSerializer, UserDetailUpdateSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, ProjectDetailSerializer
from rest_framework_simplejwt.exceptions import TokenError as SimpleJWTTokenError, ExpiredTokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from .tasks import send_otp_email, send_password_reset_email
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.timezone import now
from project.models import Project
from rest_framework import status
from django.conf import settings
from datetime import timedelta
from .models import Accounts
import requests





# Create your views here.

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        phone_number = request.data.get("phone_number")

        existing_user = Accounts.objects.filter(email=email).first()

        if existing_user:
            if existing_user.otp_verified:
                return Response({"error": "Account already exists."}, status=status.HTTP_400_BAD_REQUEST)
            elif existing_user.google_verified:
                return Response({"error": "Try another login method."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                send_otp_email.delay(existing_user.id, existing_user.email)

                return Response({"otp_verification": "OTP sent again. Please verify your email."}, status=status.HTTP_200_OK)
        print("data",request.data)
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully. OTP sent to email."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VerifyOTPView(APIView):
    permission_classes = [AllowAny] 
    
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("its comming")
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            response = Response(data, status=status.HTTP_200_OK)

            response.set_cookie(
                key="access",
                value=data["access_token"],
                httponly=True,
                secure=True, 
                samesite="None",  
                expires=now() + timedelta(minutes=1),
            )

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProtectedUserView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):

        user = request.user 
        serializer = UserSerializer(user)  
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")  
        
        if not refresh_token:
            print("Refresh token not provided in request body.")
            return Response(
                {"detail": "Refresh token not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        if not serializer.is_valid():
            print("Token refresh serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        response = Response(data, status=status.HTTP_200_OK)

        if "access" in data:
            response.set_cookie(
                key="access",
                value=data["access"],
                httponly=True,
                secure=True,
                samesite="None",
                expires=now() + timedelta(minutes=1), 
            )
        return response


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        google_credential = request.data.get("credential")

        if not google_credential:
            return Response({"error": "No credential received"}, status=status.HTTP_400_BAD_REQUEST)

        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {google_credential}"}
        user_response = requests.get(user_info_url, headers=headers)
        user_info = user_response.json()


        if "email" not in user_info:
            return Response({"error": "Failed to retrieve user information"}, status=status.HTTP_400_BAD_REQUEST)

        user, created = Accounts.objects.get_or_create(
            email=user_info["email"],
            defaults={
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
                "profile_picture": user_info.get("picture", ""),
                "google_verified": True,
                "is_active": True,
            },
        )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response_data = {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number":user.phone_number,
                "profile_picture":user.profile_picture,
                "is_superuser": user.is_superuser,
            },
            "access_token": str(access),  
            "refresh_token": str(refresh),
        }

        response = Response(response_data, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access",
            value=str(access),
            httponly=True,
            secure=True, 
            samesite="None",  
            expires=now() + timedelta(minutes=15),
        )

        return response


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except ExpiredTokenError:
                print("Token already expired — skipping blacklist.")
            except SimpleJWTTokenError as e:
                print("Other token error:", e)
            except Exception as e:
                print("Unexpected logout error:", e)

        response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        response.set_cookie("access", "", max_age=0, httponly=True, samesite="None", secure=True)

        return response



class SaveProfileImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        image_urls = request.data.get("image_urls", [])

        if not image_urls:
            return Response({"error": "No image URLs provided"}, status=400)

        try:
            user.profile_picture = image_urls[0] 
            user.save()
            return Response({"message": "Profile picture updated", "image_urls": image_urls})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        



class UserDetailUpdateView(UpdateAPIView):
    serializer_class = UserDetailUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    




class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("currentPassword")
        new_password = request.data.get("newPassword")
        confirm_password = request.data.get("confirmPassword")

        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_406_NOT_ACCEPTABLE)

        if new_password != confirm_password:
            return Response({"error": "New passwords do not match."}, status=status.HTTP_406_NOT_ACCEPTABLE)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
    



class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        
        try:
            user = Accounts.objects.get(email=email)
        except Accounts.DoesNotExist:
            return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        send_password_reset_email.delay(email, reset_link)

        return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)
    

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Accounts.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid token or user"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Token is invalid or expired"}, status=400)

        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['password'])
        user.save()

        return Response({"message": "Password has been reset successfully."}, status=200)    
    


class ProjectDetailView(RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id' 