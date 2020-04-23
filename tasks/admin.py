from django.contrib import admin
from .models import TaskList, Task, Massage


@admin.register(TaskList)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['equip', 'name']
    list_filter = ['equip']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['facility', 'status', 'title', 'created_at']
    list_filter = ['status']


@admin.register(Massage)
class MassageAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'memo', 'created_at']
    list_filter = ['task', 'author']
