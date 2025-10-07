from django.db import models
from django.conf import settings
from django.utils import timezone
from site_core.models import Category  # Import the global category

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
    ]
    
    LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # FIX: Use the global Category model
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='jobs',
        limit_choices_to={'category_type': 'job'}
    )
    
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    location = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateTimeField()
    spots_total = models.PositiveIntegerField(default=1)
    spots_left = models.PositiveIntegerField(default=1)
    level_requirement = models.CharField(max_length=20, choices=LEVELS, default='entry')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # FIX: Use consistent related_name
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobs_posted'  # Changed to avoid conflict
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    views_count = models.PositiveIntegerField(default=0)
    
    # FIX: Use consistent related_name for favorites
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='favorite_jobs',  # Keep this consistent
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.deadline and self.deadline < timezone.now():
            self.spots_left = 0
        super().save(*args, **kwargs)

    def is_active(self):
        return (
            self.status == 'approved' and
            self.spots_left > 0 and
            self.deadline > timezone.now()
        )

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])


class JobPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='purchases')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_purchases')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_sales')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purchased_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Additional notes or requirements")

    class Meta:
        ordering = ['-purchased_at']
        unique_together = ['job', 'buyer']  # Prevent duplicate purchases

    def __str__(self):
        return f"{self.job.title} - {self.buyer.username}"

    def save(self, *args, **kwargs):
        if not self.seller_id:
            self.seller = self.job.posted_by
        if not self.net_amount:
            self.net_amount = self.purchase_price - self.admin_fee - self.commission_amount
        super().save(*args, **kwargs)