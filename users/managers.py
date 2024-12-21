from django.contrib.auth.models import UserManager


class ACJUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        from users.models import UserRole
        admin_role = UserRole.objects.get(role="admin")
        extra_fields["role"] = admin_role

        return super().create_superuser(username, email, password, **extra_fields)
