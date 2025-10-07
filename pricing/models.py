from django.db import models
from django.conf import settings
from django.utils import timezone

class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('mentorship', 'Mentorship'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30, help_text="Plan duration in days")
    features = models.JSONField(default=list, help_text="List of features as strings")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return self.get_name_display()

class SubscriptionPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription_purchases')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='purchases')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    transaction = models.OneToOneField('payments.Transaction', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    def save(self, *args, **kwargs):
        if self.status == 'active' and not self.start_date:
            self.start_date = timezone.now()
            if self.plan.duration_days:
                self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'active' and (not self.end_date or self.end_date > timezone.now())

    def activate(self):
        self.status = 'active'
        self.start_date = timezone.now()
        if self.plan.duration_days:
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
        self.save()