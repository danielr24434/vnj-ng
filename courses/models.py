from django.db import models
from django.conf import settings
from django.utils import timezone
from site_core.models import Category  # import the global one


class CourseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    MODES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='courses')
    level = models.CharField(max_length=20, choices=LEVELS, default='beginner')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses_taught')
    duration = models.PositiveIntegerField(help_text="Duration in hours")
    mode = models.CharField(max_length=20, choices=MODES, default='online')
    start_date = models.DateTimeField()
    is_self_paced = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spots_total = models.PositiveIntegerField(default=1)
    spots_left = models.PositiveIntegerField(default=1)
    preview_video = models.URLField(blank=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='courses',
        limit_choices_to={'category_type': 'course'}  # only show "course" categories
    )


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def instructor_bio(self):
        return self.instructor.profile.bio

    def is_available(self):
        return (self.status == 'approved' and 
                self.spots_left > 0 and 
                (self.is_self_paced or self.start_date > timezone.now()))

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    promo_code_used = models.ForeignKey('PromoCode', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['course', 'student']

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        return (self.is_active and 
                self.used_count < self.max_uses and 
                self.valid_until > timezone.now())


class CoursePurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='purchases')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_purchases')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_sales')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purchased_at = models.DateTimeField(auto_now_add=True)
    promo_code_used = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-purchased_at']
        unique_together = ['course', 'buyer']  # Prevent duplicate purchases

    def __str__(self):
        return f"{self.course.title} - {self.buyer.username}"

    def save(self, *args, **kwargs):
        if not self.seller_id:
            self.seller = self.course.instructor
        if not self.net_amount:
            self.net_amount = self.purchase_price - self.admin_fee - self.commission_amount
        super().save(*args, **kwargs)