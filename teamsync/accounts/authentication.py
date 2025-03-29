from rest_framework_simplejwt.tokens import AccessToken, BlacklistedToken
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model


User = get_user_model()

class JWTAuthenticationFromCookies(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("access")

        if not access_token:
            return None  

        try:
            token = AccessToken(access_token)
            user = User.objects.get(id=token["user_id"])

            if BlacklistedToken.objects.filter(token__jti=token["jti"]).exists():
                return None 

        except User.DoesNotExist:
            return None  

        except Exception as e:
            return None 

        return (user, token)
