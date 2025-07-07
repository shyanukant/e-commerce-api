"""
User profile extension for Django's built-in User model.
Stores additional user information (address, phone, etc.).
"""
from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class UserProfile(models.Model):
    """
    Extends the built-in User model with additional profile fields.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')  # Linked user
    address = models.TextField(blank=True)  # User's address
    phone = models.CharField(max_length=20, blank=True)  # User's phone number
    # Add more fields as needed

    def __str__(self):
        return self.user.username


class AdminActionLog(models.Model):
    """
    Logs admin actions (create, update, delete) on key models for audit purposes.
    Stores user, action, model, object_id, object_repr, changes, and timestamp.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Acting admin/staff
    action = models.CharField(max_length=20)  # 'create', 'update', 'delete'
    model = models.CharField(max_length=100)  # Model name
    object_id = models.CharField(max_length=100)  # Object PK
    object_repr = models.TextField()  # String representation of the object
    changes = models.JSONField(null=True, blank=True)  # For updates: {field: [old, new]}
    timestamp = models.DateTimeField(auto_now_add=True)  # When the action occurred

    def __str__(self):
        return f"{self.timestamp}: {self.user} {self.action} {self.model} {self.object_id}"
