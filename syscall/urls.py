from django.contrib import admin
from django.urls import path, include

from syscall.views import home_view

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls'))
]
