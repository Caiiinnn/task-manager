from django.contrib import admin
from .models import Task, Category, TaskChecklistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'user', 'created_at']
    list_filter = ['user']
    search_fields = ['name']


class TaskChecklistItemInline(admin.TabularInline):
    model = TaskChecklistItem
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'user', 'created_at']
    search_fields = ['title', 'description']
    inlines = [TaskChecklistItemInline]
    readonly_fields = ['created_at', 'updated_at', 'completed_at']