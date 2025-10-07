from django.db import models
from django.conf import settings
from django.utils import timezone

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
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='jobs')
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    location = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateTimeField()
    spots_total = models.PositiveIntegerField(default=1)
    spots_left = models.PositiveIntegerField(default=1)
    level_requirement = models.CharField(max_length=20, choices=LEVELS, default='entry')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    views_count = models.PositiveIntegerField(default=0)
    favorites = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='my_favorite_jobs', blank=True)
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
        return (self.status == 'approved' and 
                self.spots_left > 0 and 
                self.deadline > timezone.now())

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])