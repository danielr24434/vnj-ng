from django import forms
from .models import SubscriptionPlan

class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'description', 'price', 'duration_days', 'features', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'features': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter each feature on a new line'}),
        }

class SubscribeForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=SubscriptionPlan.objects.filter(is_active=True))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan'].label_from_instance = lambda obj: f"{obj.get_name_display()} - {obj.price}"