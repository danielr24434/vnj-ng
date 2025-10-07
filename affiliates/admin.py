from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import Referral, AffiliateSale, AffiliateSettings

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'joined_at', 'is_active')
    list_filter = ('is_active', 'joined_at')
    search_fields = ('referrer__username', 'referred_user__username')
    readonly_fields = ('joined_at',)

@admin.register(AffiliateSale)
class AffiliateSaleAdmin(admin.ModelAdmin):
    list_display = ('referral', 'commission_amount', 'commission_rate', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at')
    search_fields = ('referral__referrer__username', 'referral__referred_user__username')
    readonly_fields = ('created_at',)
    actions = ['approve_commissions', 'mark_as_paid']
    
    def approve_commissions(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} commissions approved.')
    approve_commissions.short_description = "Approve selected commissions"
    
    def mark_as_paid(self, request, queryset):
        for sale in queryset:
            sale.mark_as_paid()
        self.message_user(request, f'{queryset.count()} commissions marked as paid.')
    mark_as_paid.short_description = "Mark selected commissions as paid"


@admin.register(AffiliateSettings)
class AffiliateSettingsAdmin(SingletonModelAdmin):
    fieldsets = (
        ('Referral Rewards', {
            'fields': ('referral_signup_reward', 'referral_commission_rate')
        }),
        ('Platform Fees', {
            'fields': ('job_posting_fee_rate', 'course_sale_fee_rate', 'product_sale_fee_rate', 'mentorship_fee_rate')
        }),
        ('Transaction Fees', {
            'fields': ('withdrawal_fee_rate', 'withdrawal_fixed_fee', 'transfer_fee_rate')
        }),
        ('Thresholds', {
            'fields': ('min_withdrawal_amount', 'min_commission_payout')
        }),
        ('Settings', {
            'fields': ('auto_approve_commissions', 'commission_payout_delay_days')
        }),
    )