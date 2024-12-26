from django.urls import path

from users.views import ACJUserAuthenticationView, ACJUserRegistrationView, EmailConfirmationView, profile_view, \
    logout_view

urlpatterns = [
    path('login/', ACJUserAuthenticationView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', ACJUserRegistrationView.as_view(), name='register'),
    path('confirm_email/<uuid:token>/', EmailConfirmationView.as_view(), name='confirm_email'),
]
