from django.contrib import admin

from users.models import UserRole, SyscallUser

admin.site.register(UserRole)
admin.site.register(SyscallUser)
