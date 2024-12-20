from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import SyscallUserManager


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


class SyscallUser(AbstractUser):
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)

    objects = SyscallUserManager()

    def __str__(self):
        return f"User: {self.username}"
