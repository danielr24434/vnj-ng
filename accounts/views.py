from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView
from django.views.generic import DetailView
from jobs.models import Job
from courses.models import Course
from products.models import Product
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DetailView, CreateView
from django.contrib import messages
from .forms import CustomUserCreationForm, UserProfileForm, BankAccountForm, CryptoWalletForm
from .models import UserProfile, BankAccount, CryptoWallet
from blog.models import BlogPost
from django.db import transaction
from affiliates.models import Referral
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DetailView, CreateView
from django.contrib import messages
from .forms import CustomUserCreationForm, UserProfileForm, BankAccountForm, CryptoWalletForm
from .models import UserProfile, BankAccount, CryptoWallet
from .forms import CustomUserCreationForm, UserProfileForm, BankAccountForm, CryptoWalletForm
from .models import UserProfile, BankAccount, CryptoWallet
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import UserBankPreference, VirtualAccount
from django.contrib import messages
from .models import KYCVerification, VirtualAccount, User
from .forms_kyc import KYCVerificationForm
from django.contrib import messages

import logging
logger = logging.getLogger(__name__)


@login_required
def kyc_verification(request):
    """KYC verification view with proper error handling and success messages"""
    try:
        kyc = request.user.kyc
    except KYCVerification.DoesNotExist:
        kyc = None

    # If KYC is already approved, redirect to success page
    if kyc and kyc.is_approved():
        messages.success(request, "Your KYC is already verified and approved!")
        return redirect('virtual_account')

    if request.method == 'POST':
        form = KYCVerificationForm(request.POST, request.FILES, instance=kyc)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    kyc_instance = form.save(commit=False)
                    kyc_instance.user = request.user
                    kyc_instance.status = 'pending'
                    kyc_instance.save()
                
                # Send notification to admin (you can implement this)
                send_kyc_submission_notification(request.user, kyc_instance)
                
                messages.success(
                    request, 
                    "✅ KYC verification submitted successfully! Our team will review your documents within 24-48 hours. You'll receive a notification once it's processed."
                )
                logger.info(f"KYC submitted successfully for user: {request.user.username}")
                return redirect('profile_view')
                
            except Exception as e:
                logger.error(f"Error saving KYC for user {request.user.username}: {str(e)}")
                messages.error(
                    request,
                    "❌ There was an error submitting your KYC. Please try again or contact support if the problem persists."
                )
        else:
            # Form has errors
            error_count = len(form.errors)
            messages.error(
                request,
                f"❌ Please correct the {error_count} error{'s' if error_count > 1 else ''} in the form below."
            )
            logger.warning(f"KYC form validation failed for user {request.user.username}: {form.errors}")
    else:
        form = KYCVerificationForm(instance=kyc)

    context = {
        'form': form,
        'kyc': kyc,
    }
    return render(request, 'accounts/profile/kyc_verification.html', context)

def send_kyc_submission_notification(user, kyc):
    """Send notification about new KYC submission"""
    # You can implement email notifications, in-app notifications, etc.
    # For now, we'll just log it
    logger.info(f"New KYC submission from {user.username} (ID: {kyc.id})")

@login_required
def virtual_account_details(request):
    """Display user's virtual accounts"""
    try:
        virtual_accounts = VirtualAccount.objects.filter(user=request.user)
        primary_account = virtual_accounts.filter(is_primary=True).first()
        
        context = {
            'virtual_accounts': virtual_accounts,
            'primary_account': primary_account,
        }
        return render(request, 'accounts/profile/virtual_account.html', context)
        
    except Exception as e:
        logger.error(f"Error fetching virtual accounts for {request.user.username}: {str(e)}")
        messages.error(request, "Error loading virtual account details.")
        return redirect('profile_view')

@login_required
def bank_preferences(request):
    """Manage user's bank preferences"""
    try:
        available_banks = MonnifyBank.objects.filter(is_active=True)
        user_preferences = UserBankPreference.objects.filter(user=request.user)
        virtual_accounts = VirtualAccount.objects.filter(user=request.user)
        
        if request.method == 'POST':
            selected_banks = request.POST.getlist('banks')
            
            # Update preferences
            UserBankPreference.objects.filter(user=request.user).delete()
            
            for bank_code in selected_banks:
                try:
                    bank = MonnifyBank.objects.get(bank_code=bank_code, is_active=True)
                    UserBankPreference.objects.create(user=request.user, bank=bank)
                except MonnifyBank.DoesNotExist:
                    pass
            
            messages.success(request, "✅ Bank preferences updated successfully!")
            return redirect('bank_preferences')

        context = {
            'available_banks': available_banks,
            'user_preferences': user_preferences,
            'virtual_accounts': virtual_accounts,
        }
        return render(request, 'accounts/profile/bank_preferences.html', context)
        
    except Exception as e:
        logger.error(f"Error in bank preferences for {request.user.username}: {str(e)}")
        messages.error(request, "Error updating bank preferences.")
        return redirect('profile_view')

@login_required
def set_primary_account(request, account_id):
    """Set a virtual account as primary"""
    try:
        account = VirtualAccount.objects.get(id=account_id, user=request.user)
        account.is_primary = True
        account.save()
        messages.success(request, f"✅ {account.bank_name} set as primary account")
    except VirtualAccount.DoesNotExist:
        messages.error(request, "❌ Account not found")
    except Exception as e:
        logger.error(f"Error setting primary account: {str(e)}")
        messages.error(request, "❌ Error setting primary account")
    
    return redirect('bank_preferences')

@login_required
def toggle_account_active(request, account_id):
    """Toggle virtual account active status"""
    try:
        account = VirtualAccount.objects.get(id=account_id, user=request.user)
        account.is_active = not account.is_active
        account.save()
        
        status = "activated" if account.is_active else "deactivated"
        messages.success(request, f"✅ {account.bank_name} account {status}")
    except VirtualAccount.DoesNotExist:
        messages.error(request, "❌ Account not found")
    except Exception as e:
        logger.error(f"Error toggling account status: {str(e)}")
        messages.error(request, "❌ Error updating account status")
    
    return redirect('bank_preferences')

@login_required
def toggle_account_active(request, account_id):
    try:
        account = VirtualAccount.objects.get(id=account_id, user=request.user)
        account.is_active = not account.is_active
        account.save()
        
        status = "activated" if account.is_active else "deactivated"
        messages.success(request, f"{account.bank_name} account {status}")
    except VirtualAccount.DoesNotExist:
        messages.error(request, "Account not found")
    
    return redirect('bank_preferences')

def check_username(request):
    username = request.GET.get("username", "").strip()
    User = get_user_model()

    if not username:
        return JsonResponse({"exists": False, "message": "Please enter a username."})

    exists = User.objects.filter(username__iexact=username).exists()

    if exists:
        return JsonResponse({"exists": True, "message": "This username is already taken."})
    else:
        return JsonResponse({"exists": False, "message": "This username is available!"})


# -------------------------
# REGISTER
# -------------------------
# -------------------------
# REGISTER
# -------------------------
def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    username = form.cleaned_data.get("username")
                    raw_password = form.cleaned_data.get("password1")
                    referral_code = form.cleaned_data.get("referral_code")

                    # Handle referral if provided
                    if referral_code:
                        try:
                            referrer = User.objects.get(referral_code=referral_code)
                            # Set the referred_by field in the user's profile
                            user.profile.referred_by = referrer
                            user.profile.save()
                            
                            # Create referral record in affiliates app
                            from affiliates.models import Referral
                            Referral.objects.create(
                                referrer=referrer,
                                referred_user=user
                            )
                            
                            messages.success(request, f"✅ Account created successfully! You were referred by {referrer.get_display_name()}.")
                        except User.DoesNotExist:
                            # This shouldn't happen due to form validation, but just in case
                            messages.warning(request, "Invalid referral code, but account was still created successfully.")

                    # Authenticate immediately after signup
                    user = authenticate(request, username=username, password=raw_password)
                    if user:
                        login(request, user)
                        if not referral_code:
                            messages.success(request, f"Welcome {user.username}, your account was created successfully!")
                        return redirect("dashboard")
                    else:
                        messages.error(request, "User created but automatic login failed. Please log in manually.")
            except Exception as e:
                import traceback
                print("❌ Registration Save Error:", e)
                print(traceback.format_exc())
                messages.error(request, f"Unexpected error: {e}")
        else:
            # Debug: print errors in console
            print("❌ Registration form errors:", form.errors.as_json())

            # Show all field errors to user
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/auth/register.html", {"form": form})



# -------------------------
# LOGIN
# -------------------------
def login_view(request):
    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")

        # allow login with email or username
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
        except User.DoesNotExist:
            username = username_or_email

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_display_name()}!")
            return redirect("dashboard")  # 👈 where you want after login
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, "accounts/auth/login.html")


# -------------------------
# LOGOUT
# -------------------------
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


class PublicProfileView(DetailView):
    model = UserProfile
    template_name = 'accounts/profile/public.html'
    context_object_name = 'profile_user'
    slug_field = 'user__username'   
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.object        # UserProfile
        user = profile.user  
        
        context.update({
            'user_jobs': Job.objects.filter(posted_by=user, status='approved')[:10],
            'user_courses': Course.objects.filter(instructor=user, status='approved')[:10],
            'user_products': Product.objects.filter(seller=user, status='approved')[:10],
            'user_blog_posts': BlogPost.objects.filter(author=user, status='published')[:10],
            'referral_count': Referral.objects.filter(referrer=user).count(),
            'total_posts': (
                Job.objects.filter(posted_by=user, status='approved').count() +
                Course.objects.filter(instructor=user, status='approved').count() +
                Product.objects.filter(seller=user, status='approved').count() +
                BlogPost.objects.filter(author=user, status='published').count()
            )
        })
        return context




@login_required
def profile_view(request):
    user = request.user
    profile = get_object_or_404(UserProfile, user=request.user)
    bank_accounts = BankAccount.objects.filter(user=request.user)
    crypto_wallets = CryptoWallet.objects.filter(user=request.user)
    primary_account = user.virtual_accounts.filter(is_primary=True).first()
    all_virtual_accounts = user.virtual_accounts.all()
    
    # Check if profile is complete
    profile_complete = all([
        profile.bio,
        profile.country,
        profile.phone_number,
        profile.profile_picture
    ])
    
    context = {
        'user': user,
        'profile': profile,
        'bank_accounts': bank_accounts,
        'crypto_wallets': crypto_wallets,
        'primary_account': primary_account,
        'virtual_accounts': all_virtual_accounts,
        'profile_complete': profile_complete,
    }
    return render(request, 'accounts/profile/view.html', context)

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile/edit.html'
    success_url = reverse_lazy('profile_view')

    def get_object(self):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

@login_required
def check_profile_complete(request):
    """Check if user profile is complete before allowing post creation"""
    profile = request.user.profile
    profile_complete = all([
        profile.bio,
        profile.country,
        profile.phone_number,
        profile.profile_picture
    ])
    
    if not profile_complete:
        messages.warning(
            request, 
            'Please complete your profile before creating content. '
            'You need to add your bio, country, phone number, and profile picture.'
        )
        return redirect('profile_edit')
    return None

@login_required
def create_job_redirect(request):
    """Redirect to profile completion if not complete"""
    check = check_profile_complete(request)
    if check:
        return check
    return redirect('job_create')

@login_required
def create_course_redirect(request):
    """Redirect to profile completion if not complete"""
    check = check_profile_complete(request)
    if check:
        return check
    return redirect('course_create')

@login_required
def create_product_redirect(request):
    """Redirect to profile completion if not complete"""
    check = check_profile_complete(request)
    if check:
        return check
    return redirect('product_create')

@login_required
def create_blog_redirect(request):
    """Redirect to profile completion if not complete"""
    check = check_profile_complete(request)
    if check:
        return check
    return redirect('blog_create')

class BankAccountCreateView(LoginRequiredMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'accounts/profile/bank_account_form.html'
    success_url = reverse_lazy('profile_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Bank account added successfully!')
        return super().form_valid(form)

class CryptoWalletCreateView(LoginRequiredMixin, CreateView):
    model = CryptoWallet
    form_class = CryptoWalletForm
    template_name = 'accounts/profile/crypto_wallet_form.html'
    success_url = reverse_lazy('profile_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Crypto wallet added successfully!')
        return super().form_valid(form)


# Password Reset Views
def password_reset_request(request):
    """First step: User enters their details to request password reset"""
    if request.method == 'POST':
        from .forms import PasswordResetRequestForm
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            
            # Create password reset token
            from .models import PasswordResetToken
            from django.utils import timezone
            
            # Invalidate any existing tokens for this user
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new token
            token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timezone.timedelta(hours=1)
            )
            
            messages.success(
                request, 
                f'Password reset link has been generated. Please use this link to reset your password: '
                f'{request.build_absolute_uri(f"/accounts/password-reset/confirm/{token.token}/")}'
            )
            return redirect('password_reset_request')
    else:
        from .forms import PasswordResetRequestForm
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/auth/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    """Second step: User enters new password using the token"""
    from .models import PasswordResetToken
    from .forms import PasswordResetConfirmForm
    
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        if not reset_token.is_valid():
            messages.error(request, 'This password reset link has expired or has already been used.')
            return redirect('password_reset_request')
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            # Update user password
            user = reset_token.user
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()
    
    return render(request, 'accounts/auth/password_reset_confirm.html', {
        'form': form,
        'token': token,
        'user': reset_token.user
    })