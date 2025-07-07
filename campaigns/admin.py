"""
Admin customizations for email templates and campaigns (bulk email to users).
"""
from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import EmailTemplate, EmailCampaign
from django.contrib.auth import get_user_model
from django_summernote.widgets import SummernoteWidget
from django.template.response import TemplateResponse

class EmailTemplateForm(forms.ModelForm):
    """
    Form for editing EmailTemplate with WYSIWYG editor.
    """
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        widgets = {
            'content': SummernoteWidget(),
        }

class EmailTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for EmailTemplate.
    Shows name, subject, and built-in status.
    """
    form = EmailTemplateForm
    list_display = ('name', 'subject', 'is_builtin', 'uploaded_at')
    search_fields = ('name', 'subject')
    list_filter = ('is_builtin', 'uploaded_at')
    readonly_fields = ('is_builtin', 'uploaded_at')
    ordering = ('-uploaded_at',)
    def has_delete_permission(self, request, obj=None):
        """Prevent staff from deleting built-in templates."""
        if obj and obj.is_builtin and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

class EmailCampaignForm(forms.ModelForm):
    """
    Form for editing EmailCampaign (template and name).
    """
    class Meta:
        model = EmailCampaign
        fields = ['template', 'name']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['template'].queryset = EmailTemplate.objects.all()
        self.fields['template'].required = True
        self.order_fields(['template', 'name'])

class EmailCampaignAdmin(admin.ModelAdmin):
    """
    Admin interface for EmailCampaign.
    Provides action to send campaign and view logs.
    """
    form = EmailCampaignForm
    list_display = ('name', 'template', 'sent_by', 'sent_at', 'recipients_count', 'status', 'preview_link')
    search_fields = ('name',)
    list_filter = ('status', 'sent_at')
    readonly_fields = ('sent_by', 'sent_at', 'recipients_count', 'status', 'log')
    actions = ['send_campaign']

    def get_urls(self):
        """Add custom admin URLs for sending and previewing campaigns."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('send/', self.admin_site.admin_view(self.send_campaign_view), name='send_email_campaign'),
            path('preview/<int:campaign_id>/', self.admin_site.admin_view(self.preview_campaign_view), name='preview_email_campaign'),
        ]
        return custom_urls + urls

    def preview_link(self, obj):
        if obj.id:
            url = reverse('backend_admin:preview_email_campaign', args=[obj.id])
            return mark_safe(f'<a href="{url}" target="_blank" title="Preview"><i class="fas fa-eye"></i></a>')
        return ''
    preview_link.short_description = 'Preview'
    preview_link.allow_tags = True

    def send_campaign(self, request, queryset):
        """Admin action to send the selected campaign (only one at a time)."""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one campaign to send.", level='warning')
            return
        campaign = queryset.first()
        return HttpResponseRedirect(reverse('backend_admin:send_email_campaign') + f'?campaign_id={campaign.id}')
    send_campaign.short_description = "Send selected campaign"

    def send_campaign_view(self, request):
        """Custom admin view to send the campaign to all users."""
        User = get_user_model()
        campaign_id = request.GET.get('campaign_id')
        campaign = None
        if campaign_id:
            campaign = EmailCampaign.objects.get(id=campaign_id)
        if request.method == 'POST':
            form = EmailCampaignForm(request.POST, instance=campaign)
            if form.is_valid():
                campaign = form.save(commit=False)
                campaign.sent_by = request.user
                users = User.objects.filter(is_active=True, is_staff=False)
                sent_count = 0
                log = []
                for user in users:
                    context = {'user': user}
                    html_content = campaign.template.content if campaign.template else ''
                    html_content = render_to_string('admin/email_campaign/email_base.html', {**context, 'content': mark_safe(html_content)})
                    subject = campaign.template.subject if campaign.template else ''
                    email = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email])
                    email.attach_alternative(html_content, "text/html")
                    try:
                        email.send()
                        sent_count += 1
                        log.append(f"Sent to {user.email}")
                    except Exception as e:
                        log.append(f"Failed to {user.email}: {e}")
                campaign.recipients_count = sent_count
                campaign.status = 'sent' if sent_count else 'failed'
                campaign.log = '\n'.join(log)
                campaign.save()
                self.message_user(request, f"Campaign sent to {sent_count} users.")
                return HttpResponseRedirect(reverse('backend_admin:campaigns_emailcampaign_changelist'))
        else:
            form = EmailCampaignForm(instance=campaign)
        context = {
            'form': form,
            'opts': self.model._meta,
            'title': 'Send Email Campaign',
            'original': campaign,
        }
        return TemplateResponse(request, 'admin/email_campaign/send_campaign.html', context)

    def preview_campaign_view(self, request, campaign_id):
        """Render a preview of the campaign email with context."""
        campaign = EmailCampaign.objects.get(id=campaign_id)
        user = request.user
        context = {
            'user': user,
            'app_name': getattr(settings, 'APP_NAME', 'Your App'),
            'content': mark_safe(campaign.template.content if campaign.template else ''),
        }
        html_content = render_to_string('admin/email_campaign/email_base.html', context)
        return TemplateResponse(request, 'admin/email_campaign/preview.html', {'html_content': html_content, 'title': 'Preview Email Campaign'})

# admin.site.register(EmailTemplate, EmailTemplateAdmin)
# admin.site.register(EmailCampaign, EmailCampaignAdmin)
