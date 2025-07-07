from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from campaigns.models import EmailTemplate, EmailCampaign
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class CampaignTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.admin_client = Client()
        self.admin_client.login(username='admin', password='adminpass')
        self.template = EmailTemplate.objects.create(name='Promo', subject='Hello', content='<b>Sale!</b>')

    def test_create_email_template(self):
        url = reverse('backend_admin:campaigns_emailtemplate_add')
        data = {'name': 'Event', 'subject': 'Event', 'content': '<p>Event</p>'}
        response = self.admin_client.post(url, data, follow=True)
        if response.status_code not in [200, 302]:
            print('Response content:', response.content)
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(EmailTemplate.objects.filter(name='Event').exists())

    def test_create_campaign(self):
        url = reverse('backend_admin:campaigns_emailcampaign_add')
        data = {'name': 'Test Campaign', 'template': self.template.id}
        response = self.admin_client.post(url, data, follow=True)
        if response.status_code not in [200, 302]:
            print('Response content:', response.content)
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(EmailCampaign.objects.filter(name='Test Campaign').exists())

    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_send_campaign_emails(self, mock_send):
        # Add a non-staff user to receive the campaign
        user = User.objects.create_user(username='user1', email='user1@example.com', password='userpass', is_staff=False)
        campaign = EmailCampaign.objects.create(name='SendTest', template=self.template)
        changelist_url = reverse('backend_admin:campaigns_emailcampaign_changelist')
        # Step 1: POST to changelist to trigger the send_campaign action
        response = self.admin_client.post(changelist_url, {
            'action': 'send_campaign',
            '_selected_action': [campaign.id],
            'index': 0,
        }, follow=True)
        # Step 2: Follow redirect to send view and POST the form
        send_url = reverse('backend_admin:send_email_campaign') + f'?campaign_id={campaign.id}'
        response = self.admin_client.post(send_url, {'name': campaign.name, 'template': self.template.id}, follow=True)
        if response.status_code not in [200, 302]:
            print('Response content:', response.status_code, response.content)
        self.assertIn(response.status_code, [200, 302])
        if not mock_send.called:
            print('Send campaign response:', response.status_code, response.content)
        self.assertTrue(mock_send.called)
