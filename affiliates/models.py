from django.db import models
from django.conf import settings
from django.utils import timezone
from solo.models import SingletonModel

class Referral(models.Model):
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['referrer', 'referred_user']

    def __str__(self):
        return f"{self.referrer.username} -> {self.referred_user.username}"

class AffiliateSale(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='sales')
    sale = models.ForeignKey('payments.Transaction', on_delete=models.CASCADE, related_name='affiliate_commissions')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Commission percentage")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Affiliate Sale: {self.referral.referrer.username} - {self.commission_amount}"

    def mark_as_paid(self):
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()


class AffiliateSettings(SingletonModel):
    """Global affiliate program settings"""
    
    # Referral rewards
    referral_signup_reward = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Fixed amount rewarded for each successful referral signup"
    )
    referral_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Percentage commission on referred user's transactions"
    )
    
    # Platform fees
    job_posting_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00,
        help_text="Percentage fee on job postings"
    )
    course_sale_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=3.00,
        help_text="Percentage fee on course sales"
    )
    product_sale_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.50,
        help_text="Percentage fee on product sales"
    )
    mentorship_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Percentage fee on mentorship enrollments"
    )
    
    # Transaction fees
    withdrawal_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.00,
        help_text="Percentage fee on withdrawals"
    )
    withdrawal_fixed_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=50.00,
        help_text="Fixed fee on withdrawals (in addition to percentage)"
    )
    transfer_fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.50,
        help_text="Percentage fee on transfers"
    )
    
    # Minimum thresholds
    min_withdrawal_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=1000.00,
        help_text="Minimum amount for withdrawals"
    )
    min_commission_payout = models.DecimalField(
        max_digits=10, decimal_places=2, default=500.00,
        help_text="Minimum commission amount before payout"
    )
    
    # Settings
    auto_approve_commissions = models.BooleanField(
        default=False,
        help_text="Automatically approve affiliate commissions"
    )
    commission_payout_delay_days = models.PositiveIntegerField(
        default=7,
        help_text="Days to wait before commission payout"
    )
    
    class Meta:
        verbose_name = "Affiliate Settings"
        verbose_name_plural = "Affiliate Settings"
    
    def __str__(self):
        return "Affiliate Program Settings"