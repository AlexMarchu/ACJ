from django.contrib import admin
from django.urls import path, include

from syscall.views import home_view
from users.views import SyscallUserPasswordResetView, SyscallUserPasswordResetConfirmView, PasswordResetCompleteView

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('password_reset/', SyscallUserPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/confirm/<uidb64>/<token>/', SyscallUserPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password_reset/complete', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
