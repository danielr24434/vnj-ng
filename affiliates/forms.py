from django import forms
from .models import AffiliateSale

class AffiliateSettingsForm(forms.Form):
    default_commission_rate = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Default commission rate in percentage"
    )