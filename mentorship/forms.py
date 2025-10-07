from django import forms
from .models import MentorshipOffer, MentorshipApplication

class MentorshipOfferForm(forms.ModelForm):
    class Meta:
        model = MentorshipOffer
        fields = [
            'title', 'description', 'expertise_area', 'price_per_hour',
            'subscription_requirement', 'max_students'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class MentorshipApplicationForm(forms.ModelForm):
    class Meta:
        model = MentorshipApplication
        fields = ['requested_duration', 'application_message']
        
    def clean_requested_duration(self):
        duration = self.cleaned_data.get('requested_duration')
        if duration and duration < 1:
            raise forms.ValidationError("Duration must be at least 1 hour.")
        return duration