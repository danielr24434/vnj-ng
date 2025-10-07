from django import forms
from .models import ManualDeposit
from django.utils import timezone

class ManualDepositForm(forms.ModelForm):
    deposit_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text="When did you make this deposit?"
    )

    class Meta:
        model = ManualDeposit
        fields = ['amount', 'depositor_name', 'deposit_date', 'screenshot']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '100', 'step': '0.01'}),
            'depositor_name': forms.TextInput(attrs={'placeholder': 'Name as it appears on bank receipt'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 100:
            raise forms.ValidationError("Minimum deposit amount is ₦100")
        return amount

    def clean_deposit_date(self):
        deposit_date = self.cleaned_data.get('deposit_date')
        if deposit_date and deposit_date > timezone.now():
            raise forms.ValidationError("Deposit date cannot be in the future")
        return deposit_date