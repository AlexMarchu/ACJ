import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from users.managers import ACJUserManager


class UserRole(models.Model):
    class RoleChoices(models.TextChoices):
        ADMIN = "admin", "Admin"
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"

    role = models.CharField(
        max_length=10,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT,
    )

    def __str__(self):
        return self.role


class ACJUser(AbstractUser):
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, default=3)
    email = models.EmailField(unique=True)

    objects = ACJUserManager()

    def __str__(self):
        return f"User: {self.username}"


class EmailConfirmationToken(models.Model):
    user = models.OneToOneField('ACJUser', on_delete=models.CASCADE)
    token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() - self.created_at < timezone.timedelta(minutes=15)

    def __str__(self):
        return f'EmailConfirmationToken(user={self.user}, token={self.token})'
