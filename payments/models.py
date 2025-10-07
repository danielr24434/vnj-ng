from django.db import models
from django.conf import settings
from accounts.models import User
from django.utils import timezone
from django.db.models import Sum
import logging

logger = logging.getLogger(__name__)


class PaymentMethod(models.Model):
    METHOD_TYPES = [
        ('auto', 'Automatic Gateway (e.g., Monnify)'),
        ('manual', 'Manual Bank Transfer'),
    ]

    name = models.CharField(max_length=100)
    method_type = models.CharField(max_length=10, choices=METHOD_TYPES, default='auto')
    is_active = models.BooleanField(default=True)
    
    # We can add instructions for manual methods here
    instructions = models.TextField(
        blank=True, 
        help_text="For manual methods, provide instructions for the user (e.g., 'Use your username as reference')."
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_method_type_display()})"
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('add_money', 'Add Money'),
        ('withdraw', 'Withdraw'),
        ('transfer', 'Transfer'),
        ('sale', 'Sale'),
        ('commission', 'Commission'),
        ('admin_fee', 'Admin Fee'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference']),
            models.Index(fields=['created_at']),
        ]
    
    @classmethod
    def get_user_balance(cls, user):
        """Calculate user's available balance"""
        completed_transactions = cls.objects.filter(
            user=user,
            status__in=['completed', 'approved']  # Include both completed and approved
        )
        
        # Credits: money coming into user's account
        credits = completed_transactions.filter(
            transaction_type__in=['add_money', 'sale', 'commission']
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Add transfer credits (money received from others)
        transfer_credits = completed_transactions.filter(
            transaction_type='transfer',
            metadata__has_key='sender_id'  # This indicates money received
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        credits += transfer_credits
        
        # Debits: money going out of user's account
        debits = completed_transactions.filter(
            transaction_type__in=['withdraw', 'admin_fee']
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Add transfer debits (money sent to others)
        transfer_debits = completed_transactions.filter(
            transaction_type='transfer',
            metadata__has_key='recipient_id'  # This indicates money sent
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        debits += transfer_debits
        
        balance = credits - debits
        logger.info(f"User {user.username} balance calculated: {balance} (Credits: {credits}, Debits: {debits})")
        
        return balance

    @classmethod
    def get_total_platform_balance(cls):
        """Calculate total platform balance"""
        completed_transactions = cls.objects.filter(status='completed')
        
        credits = completed_transactions.filter(
            transaction_type__in=['add_money', 'admin_fee']
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        debits = completed_transactions.filter(
            transaction_type__in=['withdraw']
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return credits - debits

    def approve(self):
        if self.status == 'pending':
            self.status = 'completed'  # Set to completed so it reflects in balance
            self.completed_at = timezone.now()
            self.save()
            return True
        return False

    def reject(self, reason):
        if self.status == 'pending':
            self.status = 'rejected'
            self.rejection_reason = reason
            self.save()
            return True
        return False
    
    def __str__(self):
            return f"{self.user.username} - {self.transaction_type} - ₦{self.amount}"

class ManualDeposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    screenshot = models.ImageField(upload_to='deposit_screenshots/')
    depositor_name = models.CharField(max_length=100, help_text="Name of person who made the deposit")
    deposit_date = models.DateTimeField(help_text="Date and time when deposit was made")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_deposits')

    class Meta:
        verbose_name = 'Manual Deposit'
        verbose_name_plural = 'Manual Deposits'

    def __str__(self):
        return f"Manual Deposit - {self.user.username} - ₦{self.amount}"