from django.contrib import admin
from django.urls import path, include

from acj.views import home_view
from users.views import ACJUserPasswordResetView, ACJUserPasswordResetConfirmView, PasswordResetCompleteView, \
    profile_view

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('problems.urls')),
    path('auth/', include('users.urls')),
    path('password_reset/', ACJUserPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/confirm/<uidb64>/<token>/', ACJUserPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password_reset/complete', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profiles/<str:username>/', profile_view, name='profile'),
]
