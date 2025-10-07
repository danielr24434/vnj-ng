from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from payments.models import Transaction
from .models import Referral, AffiliateSale, AffiliateSettings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transaction)
def handle_affiliate_commission(sender, instance, created, **kwargs):
    """Handle affiliate commissions when transactions are completed"""
    
    if not created and instance.status == 'completed':
        try:
            settings = AffiliateSettings.get_solo()
            
            # Check if user was referred
            try:
                referral = Referral.objects.get(referred_user=instance.user, is_active=True)
            except Referral.DoesNotExist:
                return  # User was not referred
            
            commission_rate = Decimal('0.00')
            
            # Determine commission rate based on transaction type
            if instance.transaction_type == 'sale':
                # This could be from job, course, product, or mentorship
                # For now, use a default rate - you can enhance this later
                commission_rate = settings.referral_commission_rate
            elif instance.transaction_type == 'add_money':
                # Small commission on money added
                commission_rate = Decimal('0.50')  # 0.5%
            else:
                return  # No commission for other transaction types
            
            if commission_rate > 0:
                commission_amount = (instance.amount * commission_rate) / Decimal('100')
                
                # Create affiliate sale record
                affiliate_sale = AffiliateSale.objects.create(
                    referral=referral,
                    sale=instance,
                    commission_amount=commission_amount,
                    commission_rate=commission_rate,
                    status='approved' if settings.auto_approve_commissions else 'pending'
                )
                
                # If auto-approved, create commission transaction
                if settings.auto_approve_commissions:
                    Transaction.objects.create(
                        user=referral.referrer,
                        transaction_type='commission',
                        amount=commission_amount,
                        status='completed',
                        description=f'Affiliate commission from {referral.referred_user.username}'
                    )
                    affiliate_sale.mark_as_paid()
                
                logger.info(f"Affiliate commission created: {commission_amount} for {referral.referrer.username}")
                
        except Exception as e:
            logger.error(f"Error processing affiliate commission: {str(e)}")

@receiver(post_save, sender=Referral)
def handle_referral_signup_reward(sender, instance, created, **kwargs):
    """Give signup reward to referrer when someone joins"""
    
    if created:
        try:
            settings = AffiliateSettings.get_solo()
            
            if settings.referral_signup_reward > 0:
                # Create reward transaction for referrer
                Transaction.objects.create(
                    user=instance.referrer,
                    transaction_type='commission',
                    amount=settings.referral_signup_reward,
                    status='completed',
                    description=f'Referral signup reward for {instance.referred_user.username}'
                )
                
                logger.info(f"Referral signup reward given: {settings.referral_signup_reward} to {instance.referrer.username}")
                
        except Exception as e:
            logger.error(f"Error processing referral signup reward: {str(e)}")