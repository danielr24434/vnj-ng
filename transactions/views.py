from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from payments.models import Transaction
from .models import Notification
from .forms import TransactionFilterForm
from .utils import mask_email


from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST

@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('/transactions/notifications')  # use the name of your notification list url


@login_required
@require_POST
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, id=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('/transactions/notifications')


@login_required
def transactions_list(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('payment_method')
    
    form = TransactionFilterForm(request.GET)
    if form.is_valid():
        transaction_type = form.cleaned_data.get('transaction_type')
        status = form.cleaned_data.get('status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if status:
            transactions = transactions.filter(status=status)
        if start_date:
            transactions = transactions.filter(created_at__date__gte=start_date)
        if end_date:
            transactions = transactions.filter(created_at__date__lte=end_date)
    
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'transactions': page_obj,
        'form': form,
    }
    return render(request, 'transactions/list.html', context)

@login_required
def transaction_detail(request, pk):
    transaction = Transaction.objects.filter(user=request.user, pk=pk).first()
    if not transaction:
        from django.http import Http404
        raise Http404("Transaction not found")
    
    context = {
        'transaction': transaction,
    }
    return render(request, 'transactions/detail.html', context)

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user)
    
    # Debug: Print notification count
    print(f"Total notifications: {notifications.count()}")
    for notification in notifications:
        print(f"Notification: {notification.title} - Read: {notification.is_read}")
    
    unread_count = notifications.filter(is_read=False).count()
    print(f"Unread count: {unread_count}")
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'unread_count': unread_count,
    }
    return render(request, 'transactions/notifications.html', context)