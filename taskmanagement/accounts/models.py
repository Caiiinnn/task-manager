from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    avatar_color = models.CharField(max_length=7, default='#6C63FF')
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username