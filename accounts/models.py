from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

# from django.contrib.postgres.fields import ArrayField  # Only if you use PostgreSQL

USERTYPE = [
    ("admin", "Admin"),
    ("viewer", "Viewer"),
    ("dept_user", "Department User"),
    ("dept_agm", "Department Chief Manager"),
    ("dept_dgm", "Department DGM"),
]


class Department(models.Model):
    department_name = models.CharField(blank=False, null=False, unique=True)

    def __str__(self):
        return self.department_name

    class Meta:
        ordering = ["department_name"]


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    user_type = models.CharField(
        choices=USERTYPE,
        max_length=50,
        blank=True,
        null=True,
    )
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    email_address = models.EmailField(
        max_length=254, unique=False, null=True, blank=True
    )
    reset_password = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["department", "user_type", "username"]
