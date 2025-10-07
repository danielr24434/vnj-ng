from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User, UserProfile

@receiver(post_save, sender=User)
def handle_referral_on_user_creation(sender, instance, created, **kwargs):
    if created and instance.referral_code:
        try:
            referrer = User.objects.get(referral_code=instance.referral_code)
            instance.profile.referred_by = referrer
            instance.profile.save()
            
            send_mail(
                'New Referral Signup',
                f'User {instance.username} has signed up using your referral code.',
                settings.DEFAULT_FROM_EMAIL,
                [referrer.email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass