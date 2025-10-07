from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.shortcuts import render
from .models import Referral, AffiliateSale
from site_core.models import SiteSetting

@login_required
def affiliate_dashboard(request):
    user = request.user
    referrals = Referral.objects.filter(referrer=user).select_related('referred_user')
    affiliate_sales = AffiliateSale.objects.filter(referral__referrer=user)
    
    total_commission = affiliate_sales.filter(status__in=['approved', 'paid']).aggregate(
        total=Sum('commission_amount')
    )['total'] or 0
    
    pending_commission = affiliate_sales.filter(status='pending').aggregate(
        total=Sum('commission_amount')
    )['total'] or 0
    
    site_settings = SiteSetting.get_solo()
    
    context = {
        'referrals': referrals,
        'total_commission': total_commission,
        'pending_commission': pending_commission,
        'referral_link': f"{request.scheme}://{request.get_host()}/ref/{user.referral_code}",
        'default_commission_rate': site_settings.default_commission_pct,
    }
    
    return render(request, 'affiliates/dashboard.html', context)

@login_required
def referral_list(request):
    user = request.user
    referrals = Referral.objects.filter(referrer=user).select_related('referred_user')
    
    for referral in referrals:
        referral.total_earned = AffiliateSale.objects.filter(
            referral=referral, 
            status__in=['approved', 'paid']
        ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    paginator = Paginator(referrals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'referrals': page_obj,
    }
    
    return render(request, 'affiliates/referrals.html', context)