"""
Models for email templates and campaigns (for bulk email to users).
"""
from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

class EmailTemplate(models.Model):
    """
    Stores reusable HTML email templates for campaigns.
    """
    name = models.CharField(max_length=100, unique=True)  # Template name
    subject = models.CharField(max_length=200)  # Email subject
    content = models.TextField(help_text="HTML content with {{ user.username }} and {{ user.get_full_name }} placeholders")  # HTML body
    is_builtin = models.BooleanField(default=False, help_text="Built-in templates cannot be deleted by staff.")  # System template flag
    uploaded_at = models.DateTimeField(auto_now_add=True)  # When template was created

    def __str__(self):
        return self.name

class EmailCampaign(models.Model):
    """
    Represents a bulk email campaign using a template.
    Tracks status, recipients, and log.
    """
    name = models.CharField(max_length=100, help_text="Internal campaign name", null=True, blank=True)  # Campaign name
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)  # Linked template
    sent_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)  # Who sent it
    sent_at = models.DateTimeField(auto_now_add=True)  # When sent
    recipients_count = models.PositiveIntegerField(default=0)  # Number of recipients
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending')  # Status
    log = models.TextField(blank=True, help_text="Log of send results (optional)")  # Send log

    def __str__(self):
        return f"{self.name} ({self.template})" if self.name else str(self.template)
