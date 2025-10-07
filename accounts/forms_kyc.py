from django import forms
from .models import KYCVerification
from django.utils import timezone
from datetime import date

class KYCVerificationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'max': timezone.now().date().isoformat(),
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200'
        }),
        help_text="Your date of birth as it appears on your ID"
    )

    class Meta:
        model = KYCVerification
        fields = [
            'id_type', 'id_number', 'legal_first_name', 'legal_last_name',
            'date_of_birth', 'address', 'city', 'state', 'country', 'postal_code',
            'id_document_front', 'id_document_back', 'selfie_with_id'
        ]
        widgets = {
            'id_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200'
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Enter your ID number exactly as it appears'
            }),
            'legal_first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Your legal first name'
            }),
            'legal_last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Your legal last name'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Your complete residential address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'State'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Country',
                'value': 'Nigeria'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Postal code (optional)'
            }),
            'id_document_front': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100'
            }),
            'id_document_back': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
            'selfie_with_id': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100'
            }),
        }
        help_texts = {
            'id_number': 'Enter your BVN, NIN, or ID number exactly as it appears on your document',
            'legal_first_name': 'Your legal first name (must match your ID document)',
            'legal_last_name': 'Your legal last name (must match your ID document)',
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise forms.ValidationError("Date of birth cannot be in the future")
        
        if dob and (date.today() - dob).days < 365 * 18:
            raise forms.ValidationError("You must be at least 18 years old to complete KYC")
        
        return dob

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        id_type = self.cleaned_data.get('id_type')
        
        if id_type == 'bvn' and (len(id_number) != 11 or not id_number.isdigit()):
            raise forms.ValidationError("BVN must be exactly 11 digits")
        
        if id_type == 'nin' and (len(id_number) != 11 or not id_number.isdigit()):
            raise forms.ValidationError("NIN must be exactly 11 digits")
            
        return id_number

    def clean_legal_first_name(self):
        first_name = self.cleaned_data.get('legal_first_name')
        if first_name and len(first_name) < 2:
            raise forms.ValidationError("First name must be at least 2 characters long")
        return first_name

    def clean_legal_last_name(self):
        last_name = self.cleaned_data.get('legal_last_name')
        if last_name and len(last_name) < 2:
            raise forms.ValidationError("Last name must be at least 2 characters long")
        return last_name