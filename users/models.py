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


class Country(models.Model):

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)

    def __str__(self):
        return f"{self.name}"


class ACJUser(AbstractUser):

    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, default=3)
    email = models.EmailField(unique=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    institution = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    objects = ACJUserManager()

    def __str__(self):
        return f"User: {self.username}"

    def is_admin(self):
        return self.role.role == UserRole.RoleChoices.ADMIN

    def is_teacher(self):
        return self.role.role == UserRole.RoleChoices.TEACHER

    def is_student(self):
        return self.role.role == UserRole.RoleChoices.STUDENT
    
    def get_name(self):
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        elif self.first_name:
            return self.first_name
        return self.username


class EmailConfirmationToken(models.Model):
    
    user = models.OneToOneField('ACJUser', on_delete=models.CASCADE)
    token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() - self.created_at < timezone.timedelta(minutes=15)

    def __str__(self):
        return f'EmailConfirmationToken(user={self.user}, token={self.token})'
