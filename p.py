from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from site_core.models import SiteSetting
from pricing.models import SubscriptionPlan
from payments.models import PaymentMethod

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed initial data for Vinaji NG'

    def handle(self, *args, **options):
        self.stdout.write('Seeding initial data...')
        
        # Create site settings
        site_settings, created = SiteSetting.objects.get_or_create(
            pk=1,
            defaults={
                'site_title': 'Vinaji NG - Work & Earn Platform',
                'site_description': 'A comprehensive platform for jobs, courses, products, and mentorship',
                'contact_email': 'support@vinaji.com',
                'currency': 'NGN',
                'currency_rate': 1.0,
                'add_money_fee_pct': 1.5,
                'transfer_fee_pct': 0.5,
                'withdraw_fee_pct': 2.0,
                'mentorship_fee_pct': 10.0,
                'default_commission_pct': 20.0,
                'default_subscription_prices': {
                    'starter': 0,
                    'pro': 5000,
                    'mentorship': 15000
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Site settings created'))
        else:
            self.stdout.write(self.style.SUCCESS('Site settings already exist'))
        
        # Create subscription plans
        plans_data = [
            {
                'name': 'starter',
                'description': 'Basic access to platform features',
                'price': 0,
                'duration_days': 30,
                'features': [
                    'Access to basic jobs',
                    'Basic course enrollment',
                    'Product purchasing',
                    'Standard support'
                ]
            },
            {
                'name': 'pro',
                'description': 'Enhanced features for professionals',
                'price': 5000,
                'duration_days': 30,
                'features': [
                    'All Starter features',
                    'Premium job listings',
                    'Advanced courses',
                    'Product selling',
                    'Priority support',
                    'Affiliate program access'
                ]
            },
            {
                'name': 'mentorship',
                'description': 'Complete platform access with mentorship',
                'price': 15000,
                'duration_days': 30,
                'features': [
                    'All Pro features',
                    'Mentorship program access',
                    'Exclusive content',
                    '1-on-1 support',
                    'Revenue sharing opportunities'
                ]
            }
        ]
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Subscription plan {plan.name} created'))
        
        # Create payment methods
        payment_methods = [
            {'name': 'monnify', 'is_active': True},
            {'name': 'paystack', 'is_active': True},
            {'name': 'bank_transfer', 'is_active': True},
            {'name': 'crypto', 'is_active': True},
        ]
        
        for method_data in payment_methods:
            method, created = PaymentMethod.objects.get_or_create(
                name=method_data['name'],
                defaults=method_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Payment method {method.name} created'))
        
        self.stdout.write(self.style.SUCCESS('Initial data seeding completed!'))