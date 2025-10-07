from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction as db_transaction
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.contrib import messages
from .models import SubscriptionPlan, SubscriptionPurchase
from .forms import SubscribeForm
from payments.models import Transaction

class PricingListView(ListView):
    model = SubscriptionPlan
    template_name = 'pricing/list.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True)

class SubscribeView(LoginRequiredMixin, CreateView):
    model = SubscriptionPurchase
    form_class = SubscribeForm
    template_name = 'pricing/subscribe.html'
    
    def form_valid(self, form):
        plan = form.cleaned_data['plan']
        user = self.request.user
        
        with db_transaction.atomic():
            subscription_purchase = form.save(commit=False)
            subscription_purchase.user = user
            subscription_purchase.amount_paid = plan.price
            
            transaction = Transaction.objects.create(
                user=user,
                amount=plan.price,
                transaction_type='withdraw',
                status='pending',
                description=f"Subscription purchase: {plan.get_name_display()}",
                metadata={
                    'plan_id': plan.id,
                    'plan_name': plan.name
                }
            )
            
            subscription_purchase.transaction = transaction
            subscription_purchase.save()
            
            messages.success(self.request, f'Subscription to {plan.get_name_display()} requested successfully.')
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('transactions_list')