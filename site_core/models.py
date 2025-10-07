from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class MonnifyBank(models.Model):
    bank_code = models.CharField(max_length=10, unique=True)
    bank_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Monnify Bank'
        verbose_name_plural = 'Monnify Banks'

    def __str__(self):
        return f"{self.bank_name} ({self.bank_code})"

class SiteSetting(models.Model):
    CURRENCY_CHOICES = [
        ('NGN', 'Nigerian Naira (NGN)'),
        ('USD', 'US Dollar (USD)'),
    ]
    
    PAYMENT_MODE_CHOICES = [
        ('manual', 'Manual Approval'),
        ('auto', 'Auto Process'),
    ]
    
    # Currency Settings
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    currency_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)
    
    # Fee Settings
    add_money_fee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=1.5)
    transfer_fee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    withdraw_fee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)
    mentorship_fee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    default_commission_pct = models.DecimalField(max_digits=5, decimal_places=2, default=20.0)
    
    # Payment Settings
    deposit_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='manual')
    withdrawal_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='manual')
    
    # Manual Payment Details
    manual_bank_name = models.CharField(max_length=100, blank=True)
    manual_account_number = models.CharField(max_length=20, blank=True)
    manual_account_name = models.CharField(max_length=100, blank=True)
    
    # Monnify Settings
    monnify_api_key = models.CharField(max_length=255, blank=True)
    monnify_secret_key = models.CharField(max_length=255, blank=True)
    monnify_contract_code = models.CharField(max_length=255, blank=True)
    monnify_base_url = models.CharField(max_length=255, default='https://api.monnify.com')
    
    # Virtual Account Settings
    default_bank_code = models.CharField(max_length=10, blank=True, help_text="Default bank for virtual accounts")
    account_reference_prefix = models.CharField(max_length=50, default='VINAJI', help_text="Prefix for account references")
    
    # Feature Toggles
    pause_course_uploading = models.BooleanField(default=False)
    pause_gigs_uploading = models.BooleanField(default=False)
    pause_affiliates = models.BooleanField(default=False)
    
    # Site Information
    site_title = models.CharField(max_length=200, default='Vinaji NG')
    site_description = models.TextField(blank=True)
    contact_email = models.EmailField(default='support@vinaji.com')
    legal_text = models.TextField(blank=True)
    
    # Default Subscription Prices
    default_subscription_prices = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Category(models.Model):
    CATEGORY_TYPES = [
        ('job', 'Job'),
        ('course', 'Course'),
        ('product', 'Product'),
        ('blog', 'Blog'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['name', 'category_type']

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"

class AdminNotification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
    ])
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    show_popup = models.BooleanField(default=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def is_current(self):
        from django.utils import timezone
        return self.is_active and self.start_date <= timezone.now() <= self.end_date