from django.contrib import admin

# Register your models here.

from .models import Template, Task, PublicHoliday, Month

admin.site.register(Template)

admin.site.register(Task)
admin.site.register(PublicHoliday)
admin.site.register(Month)
