from django.contrib import admin

# Register your models here.

from .models import Template, Task, PublicHoliday, Month, TaskRemark


admin.site.register(Month)
admin.site.register(TaskRemark)


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ("name_of_holiday", "holiday_date")

    @admin.display(description="Holiday date", ordering="date_of_holiday")
    def holiday_date(self, obj):
        # Format the date as 'YYYY-MM-DD'
        return obj.date_of_holiday.strftime("%d/%m/%Y")

    list_filter = (("date_of_holiday", admin.DateFieldListFilter),)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = (
        "task_name",
        "type_of_due_date",
        "department",
        "type_of_compliance",
        "recurring_interval",
        "recurring_task_status",
    )
    search_fields = (
        "task_name",
        "type_of_due_date",
        "department__department_name",
        "type_of_compliance",
        "recurring_interval",
        "recurring_task_status",
    )
    list_filter = (
        "type_of_due_date",
        "department",
        "type_of_compliance",
        "recurring_interval",
        "recurring_task_status",
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "task_name",
        "due_date_formatted",
        "current_status",
        "department",
        "type_of_compliance",
    )
    search_fields = (
        "task_name",
        "current_status",
        "department__department_name",
        "type_of_compliance",
    )
    list_filter = (
        "current_status",
        "department",
        ("due_date", admin.DateFieldListFilter),
        "type_of_compliance",
    )

    @admin.display(description="Due date", ordering="due_date")
    def due_date_formatted(self, obj):
        # Format the date as 'YYYY-MM-DD'
        if obj.due_date is None:
            return "-"
        return obj.due_date.strftime("%d/%m/%Y")
