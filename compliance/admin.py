from django.contrib import admin

# Register your models here.

from .models import Template, Task

admin.site.register(Template)

admin.site.register(Task)
