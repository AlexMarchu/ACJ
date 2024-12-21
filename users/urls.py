from django.urls import path

from users.views import ACJUserAuthenticationView, ACJUserRegistrationView, EmailConfirmationView

urlpatterns = [
    path('login/', ACJUserAuthenticationView.as_view(), name='login'),
    path('register/', ACJUserRegistrationView.as_view(), name='register'),
    path('confirm_email/<uuid:token>/', EmailConfirmationView.as_view(), name='confirm_email'),
]
