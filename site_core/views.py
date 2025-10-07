from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from jobs.models import Job
from django.views.decorators.http import require_POST
from courses.models import Course
from products.models import Product
from blog.models import BlogPost
from accounts.models import User, UserProfile
from payments.models import Transaction
from affiliates.models import Referral, AffiliateSale
from .models import SiteSetting, Category, AdminNotification
from .forms import SiteSettingForm, CategoryForm, AdminNotificationForm
from payments.monnify_service import MonnifyService
from django.db import transaction
from accounts.models import KYCVerification, VirtualAccount, User
from .models import MonnifyBank
from payments.models import PaymentMethod, ManualDeposit
from payments.forms import PaymentMethodForm



@staff_member_required
def manual_deposit_detail(request, deposit_id):
    deposit = get_object_or_404(ManualDeposit, id=deposit_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        with transaction.atomic():
            if action == 'approve' and deposit.status == 'pending':
                # Create a transaction record to credit the user's wallet
                Transaction.objects.create(
                    user=deposit.user,
                    transaction_type='add_money',
                    amount=deposit.amount,
                    status='completed',
                    reference=f"MANUAL_DEP_{deposit.id}",
                    description=f"Manual deposit approved. Depositor: {deposit.depositor_name}",
                    completed_at=timezone.now()
                )
                deposit.status = 'approved'
                deposit.reviewed_by = request.user
                deposit.reviewed_at = timezone.now()
                deposit.save()
                messages.success(request, f"Deposit of ₦{deposit.amount} for {deposit.user.username} has been approved and wallet credited.")
            
            elif action == 'reject' and deposit.status == 'pending':
                admin_notes = request.POST.get('admin_notes', 'No reason provided.')
                deposit.status = 'rejected'
                deposit.admin_notes = admin_notes
                deposit.reviewed_by = request.user
                deposit.reviewed_at = timezone.now()
                deposit.save()
                messages.warning(request, f"Deposit for {deposit.user.username} has been rejected.")
        
        return redirect('financial_management')

    context = {'deposit': deposit}
    return render(request, 'admin_panel/manual_deposit_detail.html', context)


@staff_member_required
def payment_settings(request):
    site_settings = SiteSetting.get_solo()
    payment_methods = PaymentMethod.objects.all()
    
    # Form for updating Gateway and Manual Bank details
    settings_form = SiteSettingForm(instance=site_settings)
    # Form for adding a new payment method
    add_method_form = PaymentMethodForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_settings':
            settings_form = SiteSettingForm(request.POST, instance=site_settings)
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, "Site payment settings have been updated successfully.")
                return redirect('payment_settings')

        elif action == 'add_method':
            add_method_form = PaymentMethodForm(request.POST)
            if add_method_form.is_valid():
                add_method_form.save()
                messages.success(request, f"Payment method '{add_method_form.cleaned_data['name']}' has been added.")
                return redirect('payment_settings')

    context = {
        'settings_form': settings_form,
        'add_method_form': add_method_form,
        'payment_methods': payment_methods
    }
    return render(request, 'admin_panel/payment_settings.html', context)


# --- NEW VIEW FOR TOGGLING PAYMENT METHOD STATUS ---
@staff_member_required
@require_POST
def toggle_payment_method(request, method_id):
    method = get_object_or_404(PaymentMethod, id=method_id)
    method.is_active = not method.is_active
    method.save()
    status = "activated" if method.is_active else "deactivated"
    messages.info(request, f"Payment method '{method.name}' has been {status}.")
    return redirect('payment_settings')



@staff_member_required
def admin_dashboard(request):
    # Basic Statistics
    total_users = User.objects.count()
    total_jobs = Job.objects.count()
    total_courses = Course.objects.count()
    total_products = Product.objects.count()
    total_blog_posts = BlogPost.objects.count()
    
    # Pending approvals
    pending_jobs = Job.objects.filter(status='pending').count()
    pending_courses = Course.objects.filter(status='pending').count()
    pending_products = Product.objects.filter(status='pending').count()
    pending_blog_posts = BlogPost.objects.filter(status='pending').count()
    
    # KYC Statistics
    kyc_stats = KYCVerification.objects.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        approved=Count('id', filter=Q(status='approved')),
        rejected=Count('id', filter=Q(status='rejected'))
    )
    
    # Financial Statistics
    total_balance = Transaction.get_total_platform_balance()
    pending_withdrawals = Transaction.objects.filter(
        transaction_type='withdraw', 
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent Activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_transactions = Transaction.objects.select_related('user').order_by('-created_at')[:10]
    
    # Top Performers (Last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    
    top_earners = Transaction.objects.filter(
        status='completed',
        created_at__gte=week_ago,
        transaction_type__in=['sale', 'commission']
    ).values('user__username').annotate(
        total_earned=Sum('amount')
    ).order_by('-total_earned')[:5]
    
    top_referrers = Referral.objects.filter(
        joined_at__gte=week_ago
    ).values('referrer__username').annotate(
        referral_count=Count('id')
    ).order_by('-referral_count')[:5]
    
    context = {
        'total_users': total_users,
        'total_jobs': total_jobs,
        'total_courses': total_courses,
        'total_products': total_products,
        'total_blog_posts': total_blog_posts,
        'pending_jobs': pending_jobs,
        'pending_courses': pending_courses,
        'pending_products': pending_products,
        'pending_blog_posts': pending_blog_posts,
        'total_balance': total_balance,
        'pending_withdrawals': pending_withdrawals,
        'recent_users': recent_users,
        'recent_transactions': recent_transactions,
        'top_earners': top_earners,
        'top_referrers': top_referrers,
        'kyc_stats': kyc_stats,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@staff_member_required
def kyc_management(request):
    kyc_list = KYCVerification.objects.select_related('user').order_by('-submitted_at')

    # Filtering
    status_filter = request.GET.get('status', '')
    if status_filter in ['pending', 'approved', 'rejected', 'needs_revision']:
        kyc_list = kyc_list.filter(status=status_filter)

    # Searching
    search_query = request.GET.get('search', '')
    if search_query:
        kyc_list = kyc_list.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(legal_first_name__icontains=search_query) |
            Q(legal_last_name__icontains=search_query) |
            Q(id_number__icontains=search_query)
        )

    # Statistics
    stats = KYCVerification.objects.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        approved=Count('id', filter=Q(status='approved')),
        rejected=Count('id', filter=Q(status='rejected'))
    )

    paginator = Paginator(kyc_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/kyc_management.html', context)


@staff_member_required
@transaction.atomic
def kyc_detail(request, kyc_id):
    kyc = get_object_or_404(KYCVerification, id=kyc_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve' and kyc.status == 'pending':
            # --- VIRTUAL ACCOUNT CREATION LOGIC ---
            monnify_service = MonnifyService()
            kyc_data = {
                'legal_first_name': kyc.legal_first_name,
                'legal_last_name': kyc.legal_last_name,
            }
            
            # Use all active banks if user has no preference, otherwise use their preferences
            preferred_banks = list(kyc.user.bank_preferences.filter(is_active=True).values_list('bank__bank_code', flat=True))
            if not preferred_banks:
                 preferred_banks = list(MonnifyBank.objects.filter(is_active=True).values_list('bank_code', flat=True))


            account_data, error = monnify_service.create_reserved_account(kyc.user, kyc_data, preferred_banks)

            if account_data and account_data.get('accounts'):
                # Delete old accounts if any, to prevent duplicates on re-approval
                VirtualAccount.objects.filter(user=kyc.user).delete()

                for account in account_data['accounts']:
                    VirtualAccount.objects.create(
                        user=kyc.user,
                        account_number=account['accountNumber'], # 823]
                        account_name=account['accountName'], # 823]
                        bank_name=account['bankName'], # 823]
                        bank_code=account['bankCode'], # 824]
                        reference=account_data['accountReference'] # 824]
                    )
                
                kyc.status = 'approved' # 825]
                kyc.rejection_reason = '' # Clear any previous rejection reason
                kyc.monnify_customer_reference = account_data.get('customerReference', '') # 825]
                kyc.reviewed_at = timezone.now() # 825]
                kyc.reviewed_by = request.user # 825]
                kyc.save()
                messages.success(request, f"KYC for {kyc.user.username} has been approved and virtual accounts have been created.")
            else:
                messages.error(request, f"Failed to create virtual accounts for {kyc.user.username}: {error}")

        elif action == 'reject' and kyc.status == 'pending':
            reason = request.POST.get('rejection_reason', 'No reason provided.')
            kyc.status = 'rejected'
            kyc.rejection_reason = reason
            kyc.reviewed_at = timezone.now()
            kyc.reviewed_by = request.user
            kyc.save()
            messages.warning(request, f"KYC for {kyc.user.username} has been rejected.")
            
        return redirect('kyc_management')

    context = {
        'kyc': kyc
    }
    return render(request, 'admin_panel/kyc_detail.html', context)



@staff_member_required
def user_management(request):
    users = User.objects.select_related('profile').all()
    
    # Filters
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'search': search,
        'status': status,
    }
    return render(request, 'admin_panel/user_management.html', context)

@staff_member_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:20]
    user_jobs = Job.objects.filter(posted_by=user)
    user_courses = Course.objects.filter(instructor=user)
    user_products = Product.objects.filter(seller=user)
    user_blog_posts = BlogPost.objects.filter(author=user)
    user_referrals = Referral.objects.filter(referrer=user)
    
    context = {
        'user': user,
        'transactions': user_transactions,
        'jobs': user_jobs,
        'courses': user_courses,
        'products': user_products,
        'blog_posts': user_blog_posts,
        'referrals': user_referrals,
    }
    return render(request, 'admin_panel/user_detail.html', context)

@staff_member_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    action = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {action}.")
    return redirect('user_management')

@staff_member_required
def category_management(request):
    categories = Category.objects.all()
    form = CategoryForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category created successfully.')
        return redirect('category_management')
    
    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'admin_panel/category_management.html', context)

@staff_member_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    form = CategoryForm(request.POST or None, instance=category)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated successfully.')
        return redirect('category_management')
    
    context = {
        'category': category,
        'form': form,
    }
    return render(request, 'admin_panel/edit_category.html', context)

@staff_member_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, 'Category deleted successfully.')
    return redirect('category_management')

@staff_member_required
def financial_management(request):
    # Withdrawal requests
    withdrawal_requests = Transaction.objects.filter(
        transaction_type='withdraw',
        status='pending'
    ).select_related('user').order_by('-created_at')
    
    # Deposit requests (if manual mode)
    deposit_requests = Transaction.objects.filter(
        transaction_type='add_money',
        status='pending'
    ).select_related('user').order_by('-created_at')
    manual_deposit_requests = ManualDeposit.objects.filter(status='pending').select_related('user')

    
    # Financial stats
    total_earnings = Transaction.objects.filter(
        transaction_type='admin_fee',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'withdrawal_requests': withdrawal_requests,
        'deposit_requests': deposit_requests,
        'total_earnings': total_earnings,
        'manual_deposit_requests': manual_deposit_requests, # Pass this to the template

    }
    return render(request, 'admin_panel/financial_management.html', context)

@staff_member_required
def process_transaction(request, transaction_id, action):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if action == 'approve':
        if transaction.approve():
            messages.success(request, 'Transaction approved successfully.')
        else:
            messages.error(request, 'Failed to approve transaction.')
    elif action == 'reject':
        transaction.reject("Rejected by admin")
        messages.success(request, 'Transaction rejected successfully.')
    
    return redirect('financial_management')

@staff_member_required
def analytics_dashboard(request):
    # Time period filter
    period = request.GET.get('period', '7')
    days = int(period)
    start_date = timezone.now() - timedelta(days=days)
    
    # User analytics
    new_users = User.objects.filter(date_joined__gte=start_date).count()
    active_users = User.objects.filter(last_login__gte=start_date).count()
    
    # Content analytics
    new_jobs = Job.objects.filter(created_at__gte=start_date).count()
    new_courses = Course.objects.filter(created_at__gte=start_date).count()
    new_products = Product.objects.filter(created_at__gte=start_date).count()
    new_posts = BlogPost.objects.filter(created_at__gte=start_date).count()
    
    # Top performers
    top_earners = Transaction.objects.filter(
        status='completed',
        created_at__gte=start_date,
        transaction_type__in=['sale', 'commission']
    ).values('user__username', 'user__profile__country').annotate(
        total_earned=Sum('amount')
    ).order_by('-total_earned')[:10]
    
    top_posters = User.objects.annotate(
        job_count=Count('posted_jobs', filter=Q(posted_jobs__created_at__gte=start_date)),
        course_count=Count('courses_taught', filter=Q(courses_taught__created_at__gte=start_date)),
        product_count=Count('products', filter=Q(products__created_at__gte=start_date)),
        post_count=Count('blog_posts', filter=Q(blog_posts__created_at__gte=start_date)),
        total_content=Count('posted_jobs', filter=Q(posted_jobs__created_at__gte=start_date)) +
                     Count('courses_taught', filter=Q(courses_taught__created_at__gte=start_date)) +
                     Count('products', filter=Q(products__created_at__gte=start_date)) +
                     Count('blog_posts', filter=Q(blog_posts__created_at__gte=start_date))
    ).filter(total_content__gt=0).order_by('-total_content')[:10]
    
    context = {
        'period': period,
        'new_users': new_users,
        'active_users': active_users,
        'new_jobs': new_jobs,
        'new_courses': new_courses,
        'new_products': new_products,
        'new_posts': new_posts,
        'top_earners': top_earners,
        'top_posters': top_posters,
    }
    return render(request, 'admin_panel/analytics.html', context)


from django.views.decorators.http import require_POST

@staff_member_required
@require_POST
def delete_notification(request, notification_id):
    notification = get_object_or_404(AdminNotification, id=notification_id)
    notification.delete()
    messages.success(request, f"Notification '{notification.title}' was deleted successfully.")
    return redirect('notification_management')


@staff_member_required
def toggle_notification(request, notification_id):
    notification = get_object_or_404(AdminNotification, id=notification_id)

    # Example: toggle "is_active" field (adjust depending on your model)
    notification.is_active = not notification.is_active
    notification.save()

    messages.success(
        request,
        f"Notification '{notification.title}' has been {'activated' if notification.is_active else 'deactivated'}."
    )
    return redirect('notification_management')


@staff_member_required
def notification_management(request):
    notifications = AdminNotification.objects.all().order_by('-created_at')
    form = AdminNotificationForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Notification created successfully.')
        return redirect('notification_management')
    
    context = {
        'notifications': notifications,
        'form': form,
    }
    return render(request, 'admin_panel/notification_management.html', context)

@staff_member_required
def site_settings(request):
    site_settings = SiteSetting.get_solo()
    form = SiteSettingForm(request.POST or None, instance=site_settings)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Site settings updated successfully.')
        return redirect('settings')
    
    context = {
        'form': form,
        'site_settings': site_settings,
    }
    return render(request, 'admin_panel/settings.html', context)

@staff_member_required
def moderation_panel(request):
    pending_jobs = Job.objects.filter(status='pending').select_related('posted_by', 'category')
    pending_courses = Course.objects.filter(status='pending').select_related('instructor', 'category')
    pending_products = Product.objects.filter(status='pending').select_related('seller', 'category')
    pending_blog_posts = BlogPost.objects.filter(status='pending').select_related('author', 'category')
    
    context = {
        'pending_jobs': pending_jobs,
        'pending_courses': pending_courses,
        'pending_products': pending_products,
        'pending_blog_posts': pending_blog_posts,
    }
    
    return render(request, 'admin_panel/moderation.html', context)