from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from payments.models import Transaction
from products.models import ProductSale
from jobs.models import Job
from courses.models import Course
from affiliates.models import Referral
from accounts.models import User

@login_required
def dashboard(request):
    user = request.user
    week_ago = timezone.now() - timedelta(days=7)
    
    # Balance and earnings
    balance_data = Transaction.get_user_balance(user)
    print(f"🧾 DEBUG: Dashboard showing balance {balance_data} for {user.username}")
    
    # Check KYC status
    try:
        kyc = user.kyc
        kyc_approved = kyc.is_approved()
    except:
        kyc = None
        kyc_approved = False
    
    # Check profile completion
    profile_complete = user.profile.is_complete if hasattr(user, 'profile') else False
    
    # This week's earnings
    weekly_earnings = Transaction.objects.filter(
        user=user,
        status='completed',
        created_at__gte=week_ago,
        transaction_type__in=['sale', 'commission']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Total earnings
    total_earnings = Transaction.objects.filter(
        user=user,
        status='completed',
        transaction_type__in=['sale', 'commission']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Active listings
    active_jobs = Job.objects.filter(posted_by=user, status='approved').count()
    active_courses = Course.objects.filter(instructor=user, status='approved').count()
    active_products = ProductSale.objects.filter(seller=user, status='completed').count()
    active_listings = active_jobs + active_courses + active_products
    
    # Referral earnings
    referral_earnings = Transaction.objects.filter(
        user=user,
        transaction_type='commission',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Top sales
    top_sales = ProductSale.objects.filter(
        seller=user, 
        status='completed'
    ).select_related('product').order_by('-net_amount')[:3]
    
    # Top products
    top_products = ProductSale.objects.filter(
        seller=user,
        status='completed'
    ).values('product__title').annotate(
        total_sales=Sum('net_amount'),
        sale_count=Count('id')
    ).order_by('-total_sales')[:5]
    
    # Recent jobs
    recent_jobs = Job.objects.filter(
        posted_by=user, 
        status='approved'
    ).order_by('-created_at')[:5]
    
    # Recent courses
    recent_courses = Course.objects.filter(
        instructor=user, 
        status='approved'
    ).order_by('-created_at')[:5]
    
    # Platform analytics (Top performers)
    top_earners_week = Transaction.objects.filter(
        status='completed',
        created_at__gte=week_ago,
        transaction_type__in=['sale', 'commission']
    ).values('user__username').annotate(
        total_earned=Sum('amount')
    ).order_by('-total_earned')[:5]
    
    top_referrers_week = Referral.objects.filter(
        joined_at__gte=week_ago
    ).values('referrer__username').annotate(
        referral_count=Count('id')
    ).order_by('-referral_count')[:5]
    recent_transactions = Transaction.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    context = {
        'balance': balance_data,
        'weekly_earnings': weekly_earnings,
        'total_earnings': total_earnings,
        'active_listings': active_listings,
        'referral_earnings': referral_earnings,
        'top_sales': top_sales,
        'top_products': top_products,
        'recent_jobs': recent_jobs,
        'recent_courses': recent_courses,
        'top_earners_week': top_earners_week,
        'top_referrers_week': top_referrers_week,
        'recent_transactions': recent_transactions,
        'profile_complete': profile_complete,
        'kyc_approved': kyc_approved,
        'kyc': kyc,
    }
    
    return render(request, 'dashboard/dashboard.html', context)