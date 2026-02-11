# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "username",
        "user_type",
        "department",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active", "user_type")
    search_fields = ("username",)
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Roles & Type",
            {"fields": ("user_type", "reset_password", "last_login", "department")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department)
