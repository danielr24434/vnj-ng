from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile, BankAccount, CryptoWallet

class CustomUserCreationForm(UserCreationForm):
    referral_code = forms.CharField(required=False, help_text="Optional referral code from another user")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
    
    def clean_referral_code(self):
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            try:
                User.objects.get(referral_code=referral_code)
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid referral code. Please check and try again.")
        return referral_code

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'subscription_level')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('bio', 'profile_picture', 'country', 'phone_number')
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell us about yourself, your skills, and experience...'
            }),
            'country': forms.TextInput(attrs={
                'placeholder': 'e.g., Nigeria, United States...'
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'e.g., +2348012345678'
            }),
        }
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not phone_number.startswith('+'):
            raise forms.ValidationError("Please include country code (e.g., +2348012345678)")
        return phone_number

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ('bank_name', 'account_number', 'account_name', 'account_type', 'is_primary')
        widgets = {
            'bank_name': forms.TextInput(attrs={'placeholder': 'e.g., GTBank, Zenith Bank'}),
            'account_number': forms.TextInput(attrs={'placeholder': '10-digit account number'}),
            'account_name': forms.TextInput(attrs={'placeholder': 'Name as it appears on bank account'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        is_primary = cleaned_data.get('is_primary')
        user = getattr(self, 'user', None)
        
        if is_primary and user:
            BankAccount.objects.filter(user=user, is_primary=True).update(is_primary=False)
        
        return cleaned_data

class CryptoWalletForm(forms.ModelForm):
    class Meta:
        model = CryptoWallet
        fields = ('crypto_type', 'wallet_address', 'network', 'is_primary')
        widgets = {
            'wallet_address': forms.TextInput(attrs={'placeholder': 'Your cryptocurrency wallet address'}),
            'network': forms.TextInput(attrs={'placeholder': 'e.g., ERC20, BEP20, TRC20'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        is_primary = cleaned_data.get('is_primary')
        user = getattr(self, 'user', None)
        
        if is_primary and user:
            CryptoWallet.objects.filter(user=user, is_primary=True).update(is_primary=False)
        
        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Enter your email address'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        email = cleaned_data.get('email')
        
        if first_name and last_name and email:
            try:
                user = User.objects.get(
                    first_name__iexact=first_name,
                    last_name__iexact=last_name,
                    email__iexact=email
                )
                cleaned_data['user'] = user
            except User.DoesNotExist:
                raise forms.ValidationError("No user found with the provided details. Please check your information.")
            except User.MultipleObjectsReturned:
                raise forms.ValidationError("Multiple users found with these details. Please contact support.")
        
        return cleaned_data


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Enter new password'
        }),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")
        
        return cleaned_data