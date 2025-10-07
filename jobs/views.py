from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from .models import Job, JobPurchase
from site_core.models import Category   # instead of JobCategory
from .forms import JobForm
from transactions.utils import get_user_balance, can_afford_purchase, create_purchase_transaction, create_sale_transaction


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib import messages

@staff_member_required
def approve_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = 'approved'
    job.save()
    messages.success(request, f"✅ Job '{job.title}' approved successfully.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@staff_member_required
def reject_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = 'rejected'
    job.save()
    messages.error(request, f"❌ Job '{job.title}' rejected.")
    return redirect(request.META.get('HTTP_REFERER', '/'))


class JobManageView(LoginRequiredMixin, ListView):
    model = Job
    template_name = 'jobs/manage.html'
    context_object_name = 'jobs'
    
    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user).select_related('category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = self.get_queryset()
        
        context.update({
            'approved_jobs': jobs.filter(status='approved').count(),
            'pending_jobs': jobs.filter(status='pending').count(),
            'rejected_jobs': jobs.filter(status='rejected').count(),
        })
        return context
    
    
class JobListView(ListView):
    model = Job
    template_name = 'jobs/list.html'
    context_object_name = 'jobs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Job.objects.filter(status='approved').select_related('posted_by', 'category')
        
        category = self.request.GET.get('category')
        job_type = self.request.GET.get('job_type')
        location = self.request.GET.get('location')
        level = self.request.GET.get('level')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__name=category)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if level:
            queryset = queryset.filter(level_requirement=level)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(company_name__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(category_type="job", is_active=True)
        return context

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/detail.html'
    context_object_name = 'job'
    
    def get_object(self):
        obj = super().get_object()
        obj.increment_views()
        return obj

from django.contrib import messages
from django.urls import reverse_lazy

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/create.html'
    
    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        form.instance.status = 'pending'
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            '✅ Your job posting has been submitted for admin approval. You will be notified once approved.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Please correct the errors below.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('jobs_list')

class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/edit.html'
    success_url = reverse_lazy('job_manage')
    
    def test_func(self):
        job = self.get_object()
        return job.posted_by == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, '✅ Job updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '❌ Please correct the errors below.')
        return super().form_invalid(form)

class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Job
    template_name = 'jobs/delete.html'
    success_url = reverse_lazy('job_manage')
    
    def test_func(self):
        job = self.get_object()
        return job.posted_by == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '✅ Job deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Purchase Views
def job_purchase_check(request, pk):
    """Check if user can afford the job and redirect accordingly."""
    job = get_object_or_404(Job, pk=pk, status='approved')
    
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to purchase this job.')
        return redirect('login')
    
    # Check if user is the job poster
    if job.posted_by == request.user:
        messages.error(request, 'You cannot purchase your own job posting.')
        return redirect('job_detail', pk=pk)
    
    # Check if already purchased
    if JobPurchase.objects.filter(job=job, buyer=request.user).exists():
        messages.info(request, 'You have already purchased this job.')
        return redirect('job_detail', pk=pk)
    
    user_balance = get_user_balance(request.user)
    
    if can_afford_purchase(request.user, job.price):
        return redirect('job_purchase_confirm', pk=pk)
    else:
        messages.warning(
            request, 
            f'Insufficient balance. You need ₦{job.price} but have ₦{user_balance}. Please add money to your account.'
        )
        return redirect('add_money')


def job_purchase_confirm(request, pk):
    """Show purchase confirmation page."""
    job = get_object_or_404(Job, pk=pk, status='approved')
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if user is the job poster
    if job.posted_by == request.user:
        messages.error(request, 'You cannot purchase your own job posting.')
        return redirect('job_detail', pk=pk)
    
    # Check if already purchased
    if JobPurchase.objects.filter(job=job, buyer=request.user).exists():
        messages.info(request, 'You have already purchased this job.')
        return redirect('job_detail', pk=pk)
    
    user_balance = get_user_balance(request.user)
    
    if not can_afford_purchase(request.user, job.price):
        messages.error(request, 'Insufficient balance.')
        return redirect('add_money')
    
    if request.method == 'POST':
        # Process the purchase
        admin_fee = job.price * 0.05  # 5% admin fee
        
        # Create purchase record
        purchase = JobPurchase.objects.create(
            job=job,
            buyer=request.user,
            seller=job.posted_by,
            purchase_price=job.price,
            admin_fee=admin_fee,
            status='completed'
        )
        
        # Create transactions
        create_purchase_transaction(
            user=request.user,
            amount=job.price,
            description=f"Purchase of job: {job.title}",
            reference=f"job_purchase_{purchase.id}"
        )
        
        create_sale_transaction(
            user=job.posted_by,
            amount=job.price,
            description=f"Sale of job: {job.title}",
            reference=f"job_sale_{purchase.id}",
            admin_fee=admin_fee
        )
        
        messages.success(request, f'✅ Successfully purchased "{job.title}"!')
        return redirect('job_purchases')
    
    context = {
        'job': job,
        'user_balance': user_balance,
        'admin_fee': job.price * 0.05,
        'net_amount': job.price - (job.price * 0.05)
    }
    
    return render(request, 'jobs/purchase_confirm.html', context)


@login_required
def job_purchases(request):
    """Show user's job purchases."""
    purchases = JobPurchase.objects.filter(buyer=request.user).order_by('-purchased_at')
    
    context = {
        'purchases': purchases,
        'title': 'My Job Purchases'
    }
    
    return render(request, 'jobs/purchases.html', context)


@login_required
def job_sales(request):
    """Show user's job sales."""
    sales = JobPurchase.objects.filter(seller=request.user).order_by('-purchased_at')
    
    context = {
        'sales': sales,
        'title': 'My Job Sales'
    }
    
    return render(request, 'jobs/sales.html', context)