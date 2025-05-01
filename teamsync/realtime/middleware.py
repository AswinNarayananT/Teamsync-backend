# realtime/middleware.py
import urllib.parse
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken, BlacklistedToken
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_str):
    try:
        token = AccessToken(token_str)
        user = User.objects.get(id=token["user_id"])
        # check blacklist
        if BlacklistedToken.objects.filter(token__jti=token["jti"]).exists():
            return None
        return user
    except Exception:
        return None

class JWTAuthMiddleware(BaseMiddleware):
    """
    Populates scope['user'] from a JWT in the cookie named 'access'.
    """

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        # Pull raw cookie header (bytes) and decode
        raw_cookie = dict(scope.get("headers", [])).get(b"cookie", b"").decode()
        # Parse into dict
        cookies = dict(pair.split("=", 1) for pair in raw_cookie.split("; ") if "=" in pair)
        access = cookies.get("access")
        if access:
            user = await get_user_from_token(access)
            if user:
                scope["user"] = user

        # Call the next middleware or application
        return await super().__call__(scope, receive, send)
