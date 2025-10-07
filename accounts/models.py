from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
import uuid


class User(AbstractUser):
    SUBSCRIPTION_CHOICES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('mentorship', 'Mentorship'),
    ]

    subscription_level = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='starter'
    )
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    is_verified = models.BooleanField(default=False)
    date_updated = models.DateTimeField(auto_now=True)

    # 🔑 Fix clashes with auth.User
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",  # use "+" if you don’t need reverse access
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",  # use "+" if you don’t need reverse access
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)

    def _generate_referral_code(self):
        code = get_random_string(8).upper()
        while User.objects.filter(referral_code=code).exists():
            code = get_random_string(8).upper()
        return code

    def get_display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    country = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # ✅ specify unique related_name to avoid confusion
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile_referrals'
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    
    @property
    def is_complete(self):
        """Check if profile is complete for content creation"""
        return all([
            self.bio,
            self.country,
            self.phone_number,
            self.profile_picture
        ])

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Need to create KYC models in accounts/models.py
class KYCApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc_application')
    legal_name = models.CharField(max_length=255)
    address = models.TextField()
    bvn = models.CharField(max_length=11, blank=True)  # BVN
    nin = models.CharField(max_length=11, blank=True)  # NIN
    nin_document = models.ImageField(upload_to='nin_documents/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BankAccount(models.Model):
    
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('current', 'Current'),
        ('business', 'Business'),
        ('domiciliary', 'Domiciliary'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

class CryptoWallet(models.Model):
    CRYPTO_TYPES = [
        ('btc', 'Bitcoin'),
        ('eth', 'Ethereum'),
        ('usdt', 'Tether'),
        ('bnb', 'Binance Coin'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crypto_wallets')
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_TYPES)
    wallet_address = models.CharField(max_length=255)
    network = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'wallet_address']

    def __str__(self):
        return f"{self.crypto_type} - {self.wallet_address[:10]}..."


# ✅ Signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()







class KYCVerification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]
    
    ID_TYPE_CHOICES = [
        ('bvn', 'Bank Verification Number (BVN)'),
        ('nin', 'National Identity Number (NIN)'),
        ('drivers_license', "Driver's License"),
        ('international_passport', 'International Passport'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    id_type = models.CharField(max_length=25, choices=ID_TYPE_CHOICES)
    id_number = models.CharField(max_length=50)
    
    # Personal Information (as required by Monnify)
    legal_first_name = models.CharField(max_length=100)
    legal_last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Nigeria')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Documents
    id_document_front = models.ImageField(upload_to='kyc_documents/')
    id_document_back = models.ImageField(upload_to='kyc_documents/', blank=True, null=True)
    selfie_with_id = models.ImageField(upload_to='kyc_documents/', blank=True, null=True)
    
    # Monnify-specific fields
    monnify_customer_reference = models.CharField(max_length=100, blank=True)
    
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_kycs')

    class Meta:
        verbose_name = 'KYC Verification'
        verbose_name_plural = 'KYC Verifications'

    def __str__(self):
        return f"KYC - {self.user.username} ({self.get_status_display()})"

    def is_approved(self):
        return self.status == 'approved'
    
    
class VirtualAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='virtual_accounts')  # Changed to ForeignKey
    account_number = models.CharField(max_length=20, unique=True)
    account_name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    reference = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'bank_code']  # One account per bank per user

    def __str__(self):
        return f"{self.account_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary account per user
            VirtualAccount.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

    
    
    
class UserBankPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_preferences')
    bank = models.ForeignKey('site_core.MonnifyBank', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'bank']
        verbose_name = 'User Bank Preference'
        verbose_name_plural = 'User Bank Preferences'

    def __str__(self):
        return f"{self.user.username} - {self.bank.bank_name}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
    
    def __str__(self):
        return f"Password Reset Token for {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 1 hour
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()