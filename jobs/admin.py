from django.contrib import admin
from .models import JobCategory, Job, JobPurchase

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'job_count')
    list_filter = ('is_active',)
    search_fields = ('name',)

    def job_count(self, obj):
        return obj.jobs.count()
    job_count.short_description = 'Jobs'

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'company_name', 'job_type', 'location',
        'salary_min', 'salary_max', 'status', 'posted_by', 'created_at'
    )
    list_filter = ('status', 'job_type', 'level_requirement', 'category', 'created_at')
    search_fields = ('title', 'company_name', 'description', 'posted_by__username')
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    list_editable = ('status',)  # Allow quick status changes
    actions = ['approve_jobs', 'reject_jobs']

    def approve_jobs(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} jobs approved successfully.')
    approve_jobs.short_description = "Approve selected jobs"

    def reject_jobs(self, request, queryset):
        for job in queryset:
            job.status = 'rejected'
            job.save()
        self.message_user(request, f'{queryset.count()} jobs rejected.')
    reject_jobs.short_description = "Reject selected jobs"


@admin.register(JobPurchase)
class JobPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'job', 'buyer', 'seller', 'purchase_price', 'admin_fee', 
        'net_amount', 'status', 'purchased_at'
    )
    list_filter = ('status', 'purchased_at')
    search_fields = ('job__title', 'buyer__username', 'seller__username')
    readonly_fields = ('purchased_at', 'net_amount')
    list_editable = ('status',)
    actions = ['mark_completed', 'mark_refunded']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} purchases marked as completed.')
    mark_completed.short_description = "Mark selected purchases as completed"

    def mark_refunded(self, request, queryset):
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} purchases marked as refunded.')
    mark_refunded.short_description = "Mark selected purchases as refunded"
