from django import forms
from payments.models import Transaction

class TransactionFilterForm(forms.Form):
    TRANSACTION_TYPES = [
        ('', 'All Types'),
        ('add_money', 'Add Money'),
        ('withdraw', 'Withdraw'),
        ('transfer', 'Transfer'),
        ('sale', 'Sale'),
        ('commission', 'Commission'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    transaction_type = forms.ChoiceField(choices=TRANSACTION_TYPES, required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))