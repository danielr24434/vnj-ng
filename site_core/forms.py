from django import forms
from .models import SiteSetting, Category, AdminNotification

# site_core/forms.py - Update the SiteSettingForm
class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = '__all__'
        widgets = {
            'site_description': forms.Textarea(attrs={'rows': 3}),
            'legal_text': forms.Textarea(attrs={'rows': 4}),
            'monnify_api_key': forms.PasswordInput(render_value=True),
            'monnify_secret_key': forms.PasswordInput(render_value=True),
            'paystack_public_key': forms.PasswordInput(render_value=True),
            'paystack_secret_key': forms.PasswordInput(render_value=True),
            'default_subscription_prices': forms.Textarea(attrs={'rows': 3, 'placeholder': '{"starter": 0, "pro": 5000, "mentorship": 15000}'}),
        }
        

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class AdminNotificationForm(forms.ModelForm):
    class Meta:
        model = AdminNotification
        fields = ['title', 'message', 'notification_type', 'action_url', 'action_text', 'show_popup', 'start_date', 'end_date']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }