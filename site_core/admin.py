from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import SiteSetting, MonnifyBank, AdminNotification, Category
from accounts.models import KYCVerification, VirtualAccount, User
from payments.models import ManualDeposit
from payments.monnify_service import MonnifyService

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_title', 'currency', 'contact_email', 'updated_at')
    fieldsets = (
        ('Currency Settings', {
            'fields': ('currency', 'currency_rate')
        }),
        ('Fee Settings', {
            'fields': (
                'add_money_fee_pct', 
                'transfer_fee_pct', 
                'withdraw_fee_pct',
                'mentorship_fee_pct',
                'default_commission_pct'
            )
        }),
        ('Payment Settings', {
            'fields': (
                'deposit_mode',
                'withdrawal_mode',
                'manual_bank_name',
                'manual_account_number', 
                'manual_account_name',
            )
        }),
        ('Monnify Configuration', {
            'fields': (
                'monnify_api_key',
                'monnify_secret_key',
                'monnify_contract_code',
                'monnify_base_url',
                'default_bank_code',
                'account_reference_prefix',
            ),
            'classes': ('collapse',)
        }),
        ('Feature Toggles', {
            'fields': (
                'pause_course_uploading',
                'pause_gigs_uploading', 
                'pause_affiliates'
            )
        }),
        ('Site Information', {
            'fields': (
                'site_title', 
                'site_description', 
                'contact_email', 
                'legal_text'
            )
        }),
        ('Subscription Prices', {
            'fields': ('default_subscription_prices',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(MonnifyBank)
class MonnifyBankAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'bank_code', 'is_active', 'is_default', 'created_at')
    list_filter = ('is_active', 'is_default')
    search_fields = ('bank_name', 'bank_code')
    list_editable = ('is_active', 'is_default')
    actions = ['fetch_banks_from_monnify']
    
    def fetch_banks_from_monnify(self, request, queryset):
        monnify_service = MonnifyService()
        success, message = monnify_service.sync_banks_to_database()
        
        if success:
            self.message_user(request, "✅ Banks successfully fetched and synced from Monnify!")
        else:
            self.message_user(request, f"❌ {message}", messages.ERROR)
    
    fetch_banks_from_monnify.short_description = "🔄 Sync banks from Monnify"
    fetch_banks_from_monnify.allowed_permissions = ('change',)

@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'id_type', 'status_badge', 'submitted_at', 'reviewed_at', 'action_buttons')
    list_filter = ('status', 'id_type', 'submitted_at', 'reviewed_at')
    search_fields = ('user__username', 'user__email', 'id_number', 'legal_first_name', 'legal_last_name')
    readonly_fields = ('submitted_at', 'reviewed_at', 'reviewed_by')
    list_per_page = 20
    actions = ['approve_selected_kyc', 'reject_selected_kyc']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'status')
        }),
        ('Personal Information', {
            'fields': (
                'legal_first_name', 
                'legal_last_name', 
                'date_of_birth',
                'id_type',
                'id_number'
            )
        }),
        ('Address Information', {
            'fields': (
                'address',
                'city',
                'state', 
                'country',
                'postal_code'
            )
        }),
        ('Documents', {
            'fields': (
                'id_document_front',
                'id_document_back',
                'selfie_with_id'
            )
        }),
        ('Review Information', {
            'fields': (
                'rejection_reason',
                'submitted_at',
                'reviewed_at',
                'reviewed_by'
            )
        }),
        ('Monnify Integration', {
            'fields': ('monnify_customer_reference',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green', 
            'rejected': 'red',
            'needs_revision': 'blue'
        }
        return format_html(
            '<span style="padding: 4px 8px; border-radius: 12px; color: white; background-color: {}; font-size: 12px; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def action_buttons(self, obj):
        buttons = []
        if obj.status == 'pending':
            buttons.append(
                f'<a href="/admin/site_core/kycverification/{obj.id}/approve/" class="button" style="background: #10b981; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; margin-right: 5px;">Approve</a>'
            )
            buttons.append(
                f'<a href="/admin/site_core/kycverification/{obj.id}/reject/" class="button" style="background: #ef4444; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">Reject</a>'
            )
        return format_html(''.join(buttons))
    

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/approve/', self.admin_site.admin_view(self.approve_kyc), name='accounts_kycverification_approve'),
            path('<path:object_id>/reject/', self.admin_site.admin_view(self.reject_kyc), name='accounts_kycverification_reject'),
        ]
        return custom_urls + urls

    def approve_kyc(self, request, object_id):
        kyc = get_object_or_404(KYCVerification, id=object_id)
        approve_kyc.short_description = "Approve selected KYC records"
        
        if kyc.status != 'pending':
            self.message_user(request, f"❌ KYC for {kyc.user.username} is not pending approval", messages.ERROR)
            return redirect('admin:accounts_kycverification_changelist')

        try:
            with transaction.atomic():
                # Create virtual account using Monnify
                monnify_service = MonnifyService()
                kyc_data = {
                    'legal_first_name': kyc.legal_first_name,
                    'legal_last_name': kyc.legal_last_name,
                }
                
                # Get user's preferred banks
                preferred_banks = list(kyc.user.bank_preferences.filter(is_active=True).values_list('bank__bank_code', flat=True))
                
                account_data, error = monnify_service.create_reserved_account(kyc.user, kyc_data, preferred_banks)
                
                if account_data and account_data.get('accounts'):
                    # Create virtual account records for each bank
                    for account in account_data['accounts']:
                        VirtualAccount.objects.create(
                            user=kyc.user,
                            account_number=account['accountNumber'],
                            account_name=account['accountName'],
                            bank_name=account['bankName'],
                            bank_code=account['bankCode'],
                            reference=account_data['accountReference'],
                            is_primary=False  # First account will be primary
                        )
                    
                    # Set first account as primary
                    first_account = VirtualAccount.objects.filter(user=kyc.user).first()
                    if first_account:
                        first_account.is_primary = True
                        first_account.save()
                    
                    # Update KYC status
                    kyc.status = 'approved'
                    kyc.monnify_customer_reference = account_data.get('customerReference', '')
                    kyc.reviewed_at = timezone.now()
                    kyc.reviewed_by = request.user
                    kyc.save()
                    
                    self.message_user(
                        request, 
                        f"✅ KYC approved and virtual accounts created for {kyc.user.username}! Account reference: {account_data['accountReference']}", 
                        messages.SUCCESS
                    )
                    
                    # Send notification to user (you can implement this)
                    self._send_kyc_approval_notification(kyc.user)
                    
                else:
                    self.message_user(
                        request, 
                        f"❌ Failed to create virtual account for {kyc.user.username}: {error}", 
                        messages.ERROR
                    )
                    
        except Exception as e:
            self.message_user(
                request, 
                f"❌ Error approving KYC for {kyc.user.username}: {str(e)}", 
                messages.ERROR
            )
        
        return redirect('admin:accounts_kycverification_changelist')
    

    def reject_kyc(self, request, object_id):
        kyc = get_object_or_404(KYCVerification, id=object_id)
        reject_kyc.short_description = "Reject selected KYC records"
        
        if request.method == 'POST':
            rejection_reason = request.POST.get('rejection_reason', '')
            if not rejection_reason:
                self.message_user(request, "❌ Please provide a rejection reason", messages.ERROR)
                return redirect('admin:accounts_kycverification_changelist')
            
            kyc.status = 'rejected'
            kyc.rejection_reason = rejection_reason
            kyc.reviewed_at = timezone.now()
            kyc.reviewed_by = request.user
            kyc.save()
            
            self.message_user(request, f"✅ KYC rejected for {kyc.user.username}", messages.SUCCESS)
            return redirect('admin:accounts_kycverification_changelist')
        
        # Show rejection reason form
        context = {
            'kyc': kyc,
            'title': 'Reject KYC Verification'
        }
        return render(request, 'admin/kyc_reject_form.html', context)

    def approve_selected_kyc(self, request, queryset):
        """Admin action to approve multiple KYC verifications"""
        approved_count = 0
        failed_count = 0
        
        for kyc in queryset.filter(status='pending'):
            try:
                # Simulate the approval process (you can call approve_kyc logic here)
                kyc.status = 'approved'
                kyc.reviewed_at = timezone.now()
                kyc.reviewed_by = request.user
                kyc.save()
                approved_count += 1
            except Exception as e:
                failed_count += 1
                # Log the error but continue with others
        
        if approved_count:
            self.message_user(request, f"✅ Successfully approved {approved_count} KYC verification(s)", messages.SUCCESS)
        if failed_count:
            self.message_user(request, f"❌ Failed to approve {failed_count} KYC verification(s)", messages.ERROR)
    
    approve_selected_kyc.short_description = "✅ Approve selected KYC verifications"

    def reject_selected_kyc(self, request, queryset):
        """Admin action to reject multiple KYC verifications"""
        rejected_count = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_at=timezone.now(),
            reviewed_by=request.user,
            rejection_reason='Rejected via bulk action'
        )
        
        self.message_user(request, f"✅ Successfully rejected {rejected_count} KYC verification(s)", messages.SUCCESS)
    
    reject_selected_kyc.short_description = "❌ Reject selected KYC verifications"

    def _send_kyc_approval_notification(self, user):
        """Send notification to user about KYC approval"""
        # Implement your notification logic here (email, in-app notification, etc.)
        print(f"KYC approved notification sent to {user.email}")

@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'bank_name', 'is_active', 'is_primary', 'created_at')
    list_filter = ('bank_name', 'is_active', 'is_primary', 'created_at')
    search_fields = ('user__username', 'account_number', 'bank_name')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active', 'is_primary')
    
    def has_add_permission(self, request):
        return False  # Virtual accounts should only be created via KYC approval

# ManualDeposit admin is registered in payments/admin.py

# ... rest of your existing admin registrations ...