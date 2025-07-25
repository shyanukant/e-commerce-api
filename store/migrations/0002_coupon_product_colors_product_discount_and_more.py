# Generated by Django 5.2.4 on 2025-07-07 04:02

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('discount', models.DecimalField(decimal_places=2, help_text='Discount percentage (e.g. 10 for 10%)', max_digits=5)),
                ('active', models.BooleanField(default=True)),
                ('expiry', models.DateTimeField(blank=True, null=True)),
                ('usage_limit', models.PositiveIntegerField(default=1)),
                ('used_count', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='colors',
            field=models.CharField(blank=True, help_text='Comma-separated colors', max_length=100),
        ),
        migrations.AddField(
            model_name='product',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Discount percentage', max_digits=5),
        ),
        migrations.AddField(
            model_name='product',
            name='coupon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='store.coupon'),
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(default=5)),
                ('review', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='store.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
