from django.db import models
from django.utils import timezone
from accounts.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6C63FF')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def progress(self):
        """Calculate automatic progress based on status and time elapsed."""
        if self.status == 'completed':
            return 100
        if self.status == 'todo':
            return 0
        if self.status == 'review':
            return 85

        # In Progress: calculate based on time elapsed vs deadline
        if self.status == 'in_progress':
            if not self.due_date:
                return 40  # Default for in-progress without deadline

            now = timezone.now()
            total_duration = (self.due_date - self.created_at).total_seconds()
            elapsed = (now - self.created_at).total_seconds()

            if total_duration <= 0:
                return 50

            ratio = elapsed / total_duration
            # Map to 10-80% range for in_progress
            progress = int(10 + (ratio * 70))
            return max(10, min(80, progress))

        return 0

    @property
    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return timezone.now() > self.due_date
        return False

    @property
    def days_until_due(self):
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now()
        return delta.days

    @property
    def time_remaining(self):
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now()
        total_seconds = int(delta.total_seconds())

        if total_seconds < 0:
            return 'Overdue'

        days = delta.days
        hours = (total_seconds % 86400) // 3600

        if days > 1:
            return f'{days} days left'
        elif days == 1:
            return f'1 day {hours}h left'
        elif hours > 0:
            return f'{hours} hours left'
        else:
            minutes = (total_seconds % 3600) // 60
            return f'{minutes} minutes left'

    @property
    def priority_weight(self):
        weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        return weights.get(self.priority, 2)

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'completed':
            self.completed_at = None
        super().save(*args, **kwargs)


class TaskChecklistItem(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    text = models.CharField(max_length=300)
    is_done = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.task.title} - {self.text}"