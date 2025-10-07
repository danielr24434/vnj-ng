from django.contrib import admin
from .models import MentorshipOffer, MentorshipApplication, Mentor, MentorshipEnrollment, MentorshipChat

@admin.register(MentorshipOffer)
class MentorshipOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentor', 'expertise_area', 'price_per_hour', 'subscription_requirement', 'current_students', 'max_students', 'status', 'created_at')
    list_filter = ('status', 'subscription_requirement', 'expertise_area', 'created_at')
    search_fields = ('title', 'description', 'mentor__username')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_offers', 'reject_offers']
    
    def approve_offers(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} mentorship offers approved.')
    approve_offers.short_description = "Approve selected offers"
    
    def reject_offers(self, request, queryset):
        for offer in queryset:
            offer.status = 'rejected'
            offer.save()
        self.message_user(request, f'{queryset.count()} offers rejected.')
    reject_offers.short_description = "Reject selected offers"

@admin.register(MentorshipApplication)
class MentorshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('mentorship_offer', 'applicant', 'requested_duration', 'total_amount', 'status', 'applied_at', 'approved_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('mentorship_offer__title', 'applicant__username')
    readonly_fields = ('applied_at', 'approved_at', 'completed_at')
    actions = ['approve_applications', 'complete_applications']
    
    def approve_applications(self, request, queryset):
        for application in queryset:
            application.approve()
        self.message_user(request, f'{queryset.count()} applications approved.')
    approve_applications.short_description = "Approve selected applications"
    
    def complete_applications(self, request, queryset):
        for application in queryset:
            application.complete()
        self.message_user(request, f'{queryset.count()} applications completed.')
    complete_applications.short_description = "Mark selected applications as completed"


# New Mentor Management System Admin
@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'expertise_area', 'price', 'available_slots', 'people_mentored_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'expertise_area', 'created_at')
    search_fields = ('name', 'username', 'expertise_area', 'bio')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'username', 'email', 'phone', 'mentor_picture')
        }),
        ('Mentorship Details', {
            'fields': ('bio', 'expertise_area', 'duration', 'price')
        }),
        ('Availability', {
            'fields': ('maximum_slots', 'slots_taken', 'people_mentored_count', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def available_slots(self, obj):
        return obj.available_slots
    available_slots.short_description = 'Available Slots'


@admin.register(MentorshipEnrollment)
class MentorshipEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'student', 'purchase_price', 'admin_fee', 'net_amount', 'status', 'enrolled_at')
    list_filter = ('status', 'enrolled_at')
    search_fields = ('mentor__name', 'mentor__username', 'student__username')
    readonly_fields = ('tracking_id', 'enrolled_at', 'completed_at', 'admin_fee', 'net_amount')
    actions = ['activate_enrollments', 'complete_enrollments']
    
    def activate_enrollments(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} enrollments activated.')
    activate_enrollments.short_description = "Activate selected enrollments"
    
    def complete_enrollments(self, request, queryset):
        from django.utils import timezone
        for enrollment in queryset:
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
            enrollment.save()
        self.message_user(request, f'{queryset.count()} enrollments completed.')
    complete_enrollments.short_description = "Complete selected enrollments"


@admin.register(MentorshipChat)
class MentorshipChatAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'sender', 'message_preview', 'is_read', 'sent_at')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('enrollment__mentor__name', 'enrollment__student__username', 'sender__username', 'message')
    readonly_fields = ('sent_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message Preview'