from django.contrib import admin
from django.utils import timezone
from .models import PaymentMethod, Transaction, ManualDeposit

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'transaction_type', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'currency', 'created_at')
    search_fields = ('reference', 'user__username', 'description')
    readonly_fields = ('reference', 'created_at', 'updated_at', 'completed_at')
    actions = ['approve_transactions', 'reject_transactions']
    
    def approve_transactions(self, request, queryset):
        approved_count = 0
        for transaction in queryset.filter(status='pending'):
            if transaction.approve():
                approved_count += 1
        self.message_user(request, f'{approved_count} transactions approved.')
    approve_transactions.short_description = "Approve selected transactions"
    
    def reject_transactions(self, request, queryset):
        for transaction in queryset:
            transaction.reject("Rejected by admin")
        self.message_user(request, f'{queryset.count()} transactions rejected.')
    reject_transactions.short_description = "Reject selected transactions"

@admin.register(ManualDeposit)
class ManualDepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'depositor_name', 'deposit_date', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'deposit_date')
    search_fields = ('user__username', 'depositor_name', 'user__email')
    readonly_fields = ('created_at', 'reviewed_at', 'reviewed_by')
    actions = ['approve_deposits', 'reject_deposits']
    
    fieldsets = (
        ('Deposit Information', {
            'fields': ('user', 'amount', 'depositor_name', 'deposit_date', 'screenshot')
        }),
        ('Review Information', {
            'fields': ('status', 'admin_notes', 'reviewed_by', 'reviewed_at', 'created_at')
        }),
    )
    
    def approve_deposits(self, request, queryset):
        approved_count = 0
        for deposit in queryset.filter(status='pending'):
            # Create a transaction for the approved deposit
            Transaction.objects.create(
                user=deposit.user,
                amount=deposit.amount,
                transaction_type='add_money',
                status='completed',
                description=f'Manual deposit approved - {deposit.depositor_name}',
                completed_at=timezone.now(),
                metadata={
                    'manual_deposit_id': deposit.id,
                    'depositor_name': deposit.depositor_name,
                    'deposit_date': deposit.deposit_date.isoformat()
                }
            )
            
            # Update deposit status
            deposit.status = 'approved'
            deposit.reviewed_at = timezone.now()
            deposit.reviewed_by = request.user
            deposit.save()
            approved_count += 1
            
        self.message_user(request, f'{approved_count} manual deposits approved and credited to user accounts.')
    approve_deposits.short_description = "Approve selected manual deposits"
    
    def reject_deposits(self, request, queryset):
        rejected_count = 0
        for deposit in queryset.filter(status='pending'):
            deposit.status = 'rejected'
            deposit.reviewed_at = timezone.now()
            deposit.reviewed_by = request.user
            if not deposit.admin_notes:
                deposit.admin_notes = "Rejected by admin"
            deposit.save()
            rejected_count += 1
            
        self.message_user(request, f'{rejected_count} manual deposits rejected.')
    reject_deposits.short_description = "Reject selected manual deposits"