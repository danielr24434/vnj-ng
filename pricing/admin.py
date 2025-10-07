from django.contrib import admin
from .models import SubscriptionPlan, SubscriptionPurchase

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('price', 'is_active')
    search_fields = ('name', 'description')

@admin.register(SubscriptionPurchase)
class SubscriptionPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount_paid', 'status', 'start_date', 'end_date', 'purchased_at')
    list_filter = ('status', 'plan', 'purchased_at')
    search_fields = ('user__username', 'plan__name')
    readonly_fields = ('purchased_at',)
    actions = ['activate_subscriptions']

    def activate_subscriptions(self, request, queryset):
        activated_count = 0
        for purchase in queryset.filter(status='pending'):
            purchase.activate()
            activated_count += 1
        self.message_user(request, f'{activated_count} subscriptions activated.')
    activate_subscriptions.short_description = "Activate selected subscriptions"