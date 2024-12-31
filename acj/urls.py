from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from acj import settings
from acj.views import home_view, problem_detail
from users.views import ACJUserPasswordResetView, ACJUserPasswordResetConfirmView, PasswordResetCompleteView, \
    profile_view, settings_view

urlpatterns = [
    path('', home_view, name='home'),
    path('contests/', include('contests.urls')),
    path('problem/<int:problem_id>/', problem_detail, name='problem_detail'),
    path('admin/', admin.site.urls),
    path('api/', include('problems.urls')),
    path('auth/', include('users.urls')),
    path('password_reset/', ACJUserPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/confirm/<uidb64>/<token>/', ACJUserPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
    path('password_reset/complete', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profiles/<str:username>/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
