from django.urls import path
from .views import RegisterView,LoginView,VerifyOTPView,ResendOTPView,ProtectedUserView,GoogleLoginView,LogoutView,SaveProfileImagesView,UserDetailUpdateView,ChangePasswordView, ForgotPasswordView, ResetPasswordView, ProjectDetailView


urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('verify-otp/',VerifyOTPView.as_view(),name="verify-otp"),
    path('resend-otp/',ResendOTPView.as_view(),name="resent-otp"),
    path('login/', LoginView.as_view(), name="login"),
    path("protected/", ProtectedUserView.as_view(), name="protected-user"),
    path("auth/google/", GoogleLoginView.as_view(), name="google_login"),
    path("save-profile-images/", SaveProfileImagesView.as_view(), name="save-profile-images"),
    path('update/', UserDetailUpdateView.as_view(), name='update'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset-password'),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('dashboard/projects/<int:id>/', ProjectDetailView.as_view(), name='project-detail'),

]
