from django.contrib import admin

from users.models import UserRole, ACJUser

admin.site.register(UserRole)
admin.site.register(ACJUser)
