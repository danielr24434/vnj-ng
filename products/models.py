from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from site_core.models import Category

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    LICENSE_TYPES = [
        ('personal', 'Personal Use'),
        ('commercial', 'Commercial Use'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPES, default='personal')
    version = models.CharField(max_length=20, default='1.0')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'category_type': 'product'}
    )

    
    # Media
    thumbnail = models.ImageField(upload_to='product_thumbnails/', blank=True, null=True)
    gallery_images = models.ManyToManyField('ProductImage', blank=True)
    
    # Files
    product_file = models.FileField(
        upload_to='product_files/',
        validators=[FileExtensionValidator(allowed_extensions=['zip', 'pdf', 'doc', 'docx'])]
    )
    sample_file = models.FileField(
        upload_to='sample_files/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png'])]
    )
    
    # Additional details
    features = models.TextField(blank=True, help_text="List of features (one per line)")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    views_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_downloads(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def get_features_list(self):
        return [feature.strip() for feature in self.features.split('\n') if feature.strip()]

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

class ProductImage(models.Model):
    image = models.ImageField(upload_to='product_gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.title}"
    



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

class ProductSale(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_purchases')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_sales')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purchased_at = models.DateTimeField(auto_now_add=True)
    license_key = models.CharField(max_length=100, blank=True)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.product.title} - {self.buyer.username}"

    def save(self, *args, **kwargs):
        if not self.license_key:
            import uuid
            self.license_key = str(uuid.uuid4())[:16].upper()
        super().save(*args, **kwargs)