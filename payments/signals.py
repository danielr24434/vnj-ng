from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from transactions.models import Notification

@receiver(post_save, sender=Transaction)
def create_transaction_notification(sender, instance, created, **kwargs):
    """Create notification when transaction is created or status changes"""
    
    if created:
        # New transaction created
        if instance.transaction_type == 'add_money':
            title = "Money Added"
            message = f"₦{instance.amount} has been added to your account."
        elif instance.transaction_type == 'withdraw':
            title = "Withdrawal Request"
            message = f"Your withdrawal request of ₦{instance.amount} is being processed."
        elif instance.transaction_type == 'transfer':
            title = "Money Transfer"
            message = f"₦{instance.amount} has been transferred."
        elif instance.transaction_type == 'sale':
            title = "Sale Completed"
            message = f"You earned ₦{instance.amount} from a sale."
        elif instance.transaction_type == 'commission':
            title = "Commission Earned"
            message = f"You earned ₦{instance.amount} in commission."
        else:
            title = "Transaction Created"
            message = f"A new {instance.get_transaction_type_display().lower()} transaction has been created."
        
        Notification.objects.create(
            user=instance.user,
            notification_type='transaction',
            title=title,
            message=message
        )
    
    else:
        # Transaction status updated
        if instance.status == 'completed':
            if instance.transaction_type == 'add_money':
                title = "Money Added Successfully"
                message = f"₦{instance.amount} has been successfully added to your account."
            elif instance.transaction_type == 'withdraw':
                title = "Withdrawal Completed"
                message = f"Your withdrawal of ₦{instance.amount} has been completed."
            else:
                title = "Transaction Completed"
                message = f"Your {instance.get_transaction_type_display().lower()} transaction has been completed."
            
            Notification.objects.create(
                user=instance.user,
                notification_type='transaction',
                title=title,
                message=message
            )
        
        elif instance.status == 'rejected':
            title = "Transaction Rejected"
            message = f"Your {instance.get_transaction_type_display().lower()} transaction has been rejected."
            
            Notification.objects.create(
                user=instance.user,
                notification_type='transaction',
                title=title,
                message=message
            )