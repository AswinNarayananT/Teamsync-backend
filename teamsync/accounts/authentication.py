from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken, OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model

User = get_user_model()

class JWTAuthenticationFromCookies(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("access")

        print(f"🔍 Cookies Received: {request.COOKIES}")
        print(f"🔍 Access Token Received: {access_token}")

        if not access_token:
            print("🚫 No access token found. Returning None (Triggers 401).")
            return None  # ✅ Returning None allows Django to return 401

        try:
            token = AccessToken(access_token)
            user = User.objects.get(id=token["user_id"])

            if BlacklistedToken.objects.filter(token__jti=token["jti"]).exists():
                print("🚫 Token is blacklisted. Returning None.")
                return None  # ✅ Returning None ensures a 401 is triggered

        except User.DoesNotExist:
            print("🚫 User not found. Returning None.")
            return None  # ✅ Triggers 401

        except Exception as e:
            print(f"⚠️ Authentication Error: {e}")
            return None  # ✅ Triggers 401

        return (user, token)
