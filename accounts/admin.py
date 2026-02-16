# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "username",
        "department",
        "is_staff",
        "is_active",
        "get_groups",
    )
    list_filter = (
        "is_staff",
        "is_active",
    )
    search_fields = ("username",)
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Roles & Type",
            {"fields": ("reset_password", "last_login", "department")},
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("groups", "department")

    def get_groups(self, obj):
        return ", ".join(group.name for group in obj.groups.all())


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department)
