from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Product
from orders.models import Order
from campaigns.models import EmailTemplate, EmailCampaign

class Command(BaseCommand):
    help = 'Create Staff group with add, change, view permissions (no delete) for key models.'

    def handle(self, *args, **options):
        staff_group, created = Group.objects.get_or_create(name='Staff')
        models = [Product, Order, EmailTemplate, EmailCampaign]
        perms = ['add', 'change', 'view']
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            for perm in perms:
                codename = f'{perm}_{model._meta.model_name}'
                try:
                    permission = Permission.objects.get(content_type=ct, codename=codename)
                    staff_group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Permission {codename} not found for {model}'))
        self.stdout.write(self.style.SUCCESS('Staff group updated with add, change, view permissions.')) 