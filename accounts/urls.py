from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile_view"),
    path("check-username/", views.check_username, name="check_username"),
   
    
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('bank-account/add/', views.BankAccountCreateView.as_view(), name='bank_account_add'),
    path('crypto-wallet/add/', views.CryptoWalletCreateView.as_view(), name='crypto_wallet_add'),
    path('kyc/', views.kyc_verification, name='kyc_verification'),
    path('virtual-account/', views.virtual_account_details, name='virtual_account'),
    path('bank-preferences/', views.bank_preferences, name='bank_preferences'),
    path('set-primary-account/<int:account_id>/', views.set_primary_account, name='set_primary_account'),
    path('toggle-account/<int:account_id>/', views.toggle_account_active, name='toggle_account_active'),
    
    # Password Reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<uuid:token>/', views.password_reset_confirm, name='password_reset_confirm'),

    # This must stay LAST to avoid catching 'edit' as username
    path('profile/<str:username>/', views.PublicProfileView.as_view(), name='public_profile'),



]