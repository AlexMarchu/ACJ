from django.urls import path

from users.views import SyscallUserAuthenticationView, SyscallUserRegistrationView, EmailConfirmationView

urlpatterns = [
    path('login/', SyscallUserAuthenticationView.as_view(), name='login'),
    path('register/', SyscallUserRegistrationView.as_view(), name='register'),
    path('confirm_email/<uuid:token>/', EmailConfirmationView.as_view(), name='confirm_email'),
]
