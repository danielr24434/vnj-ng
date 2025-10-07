from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, BankAccount, CryptoWallet, PasswordResetToken


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = "user"   # ✅ Tell Django to use the OneToOne field, not referred_by
    can_delete = False


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'subscription_level', 'is_verified', 'date_joined')
    list_filter = ('subscription_level', 'is_verified', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Vinaji Profile', {
            'fields': ('subscription_level', 'referral_code', 'is_verified')
        }),
    )
    inlines = [UserProfileInline]


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank_name', 'account_number', 'account_name', 'is_primary', 'is_verified')
    list_filter = ('bank_name', 'is_primary', 'is_verified')
    search_fields = ('user__username', 'account_number', 'account_name')


@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'crypto_type', 'wallet_address_short', 'is_primary')
    list_filter = ('crypto_type', 'is_primary')
    search_fields = ('user__username', 'wallet_address')

    def wallet_address_short(self, obj):
        return f"{obj.wallet_address[:10]}..." if obj.wallet_address else ""
    wallet_address_short.short_description = 'Wallet Address'


admin.site.register(User, CustomUserAdmin)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used', 'is_valid')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'
