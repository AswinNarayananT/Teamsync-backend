from django.urls import path
from .views import RegisterView,LoginView,VerifyOTPView,ResendOTPView,ProtectedUserView,GoogleLoginView,LogoutView


urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('verify-otp/',VerifyOTPView.as_view(),name="verify-otp"),
    path('resent-otp/',ResendOTPView.as_view(),name="resent-otp"),
    path('login/', LoginView.as_view(), name="login"),
    path("protected/", ProtectedUserView.as_view(), name="protected-user"),
    path("auth/google/", GoogleLoginView.as_view(), name="google_login"),
    path('logout/', LogoutView.as_view(), name="logout"),

]
