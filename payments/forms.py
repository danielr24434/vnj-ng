from django import forms
from .models import Transaction
from .models import PaymentMethod
class AddMoneyForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '100', 'step': '0.01'})
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 100:
            raise forms.ValidationError("Minimum amount to add is 100.")
        return amount

class WithdrawForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '500', 'step': '0.01'})
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 500:
            raise forms.ValidationError("Minimum withdrawal amount is 500.")
        return amount

class TransferForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=100)
    recipient_username = forms.CharField(max_length=150)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    
    def clean_recipient_username(self):
        from accounts.models import User
        username = self.cleaned_data.get('recipient_username')
        try:
            recipient = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")
        return recipient
    
    
    from .models import PaymentMethod

# /vinaji_project/payments/forms.py
from django import forms
from .models import PaymentMethod, ManualDeposit
from django.utils import timezone

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name', 'method_type', 'instructions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'e.g., Monnify Auto Funding'
            }),
            'method_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded'
            })
        }

class ManualDepositForm(forms.ModelForm):
    class Meta:
        model = ManualDeposit
        fields = ['amount', 'depositor_name', 'deposit_date', 'screenshot']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'required': True}),
            'depositor_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'required': True}),
            'deposit_date': forms.DateTimeInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'type': 'datetime-local', 'required': True}),
            'screenshot': forms.FileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100', 'required': True}),
        }

    def clean_deposit_date(self):
        deposit_date = self.cleaned_data.get('deposit_date')
        if deposit_date and deposit_date > timezone.now():
            raise forms.ValidationError("Deposit date cannot be in the future.")
        return deposit_date
        
    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #     if not instance.config:
    #         instance.config = {}
    #     if commit:
    #         instance.save()
    #     return instance