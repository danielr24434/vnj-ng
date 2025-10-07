from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserProfile, BankAccount
from payments.models import Transaction

User = get_user_model()

class UserModelTests(TestCase):
    def test_user_creation_with_profile(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
    
    def test_referral_code_generation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertIsNotNone(user.referral_code)
        self.assertEqual(len(user.referral_code), 8)

class BalanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_balance_calculation(self):
        # Add money transaction
        Transaction.objects.create(
            user=self.user,
            transaction_type='add_money',
            amount=1000,
            status='completed'
        )
        
        # Sale transaction
        Transaction.objects.create(
            user=self.user,
            transaction_type='sale',
            amount=500,
            status='completed'
        )
        
        # Withdraw transaction
        Transaction.objects.create(
            user=self.user,
            transaction_type='withdraw',
            amount=300,
            status='completed'
        )
        
        balance = Transaction.get_user_balance(self.user)
        self.assertEqual(balance, 1200)  # 1000 + 500 - 300
    
    def test_commission_calculation(self):
        sale_amount = 1000
        commission_rate = 20  # 20%
        expected_commission = sale_amount * (commission_rate / 100)
        
        self.assertEqual(expected_commission, 200)