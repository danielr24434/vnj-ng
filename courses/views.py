from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from .models import Course, Enrollment, PromoCode, CoursePurchase
from .forms import CourseForm
from site_core.models import Category
from transactions.utils import get_user_balance, can_afford_purchase, create_purchase_transaction, create_sale_transaction



from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib import messages

@staff_member_required
def approve_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.status = 'approved'
    course.save()
    messages.success(request, f"✅ Course '{course.title}' approved successfully.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@staff_member_required
def reject_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.status = 'rejected'
    course.save()
    messages.error(request, f"❌ Course '{course.title}' rejected.")
    return redirect(request.META.get('HTTP_REFERER', '/'))




class CourseListView(ListView):
    model = Course
    template_name = 'courses/list.html'
    context_object_name = 'courses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Course.objects.filter(status='approved').select_related('instructor', 'category')
        
        category = self.request.GET.get('category')
        level = self.request.GET.get('level')
        mode = self.request.GET.get('mode')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__name=category)
        if level:
            queryset = queryset.filter(level=level)
        if mode:
            queryset = queryset.filter(mode=mode)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(category_type="course", is_active=True)
        return context

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/detail.html'
    context_object_name = 'course'

from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/create.html'
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        form.instance.status = 'pending'
        response = super().form_valid(form)
        
        # Add success message
        messages.success(
            self.request, 
            '✅ Your course has been submitted for admin approval. You will be notified once approved.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Please correct the errors below.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses_list')



class CourseManageView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/manage.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user).select_related('category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = self.get_queryset()
        
        context.update({
            'approved_courses': courses.filter(status='approved').count(),
            'pending_courses': courses.filter(status='pending').count(),
            'rejected_courses': courses.filter(status='rejected').count(),
        })
        return context
    
    
class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/edit.html'
    success_url = reverse_lazy('courses_list')
    
    def test_func(self):
        course = self.get_object()
        return course.instructor == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, '✅ Course updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '❌ Please correct the errors below.')
        return super().form_invalid(form)

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/delete.html'
    success_url = reverse_lazy('course_manage')
    
    def test_func(self):
        course = self.get_object()
        return course.instructor == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '✅ Course deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Purchase Views
def course_purchase_check(request, pk):
    """Check if user can afford the course and redirect accordingly."""
    course = get_object_or_404(Course, pk=pk, status='approved')
    
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to purchase this course.')
        return redirect('login')
    
    # Check if user is the course instructor
    if course.instructor == request.user:
        messages.error(request, 'You cannot purchase your own course.')
        return redirect('course_detail', pk=pk)
    
    # Check if already purchased
    if CoursePurchase.objects.filter(course=course, buyer=request.user).exists():
        messages.info(request, 'You have already purchased this course.')
        return redirect('course_detail', pk=pk)
    
    user_balance = get_user_balance(request.user)
    
    if can_afford_purchase(request.user, course.price):
        return redirect('course_purchase_confirm', pk=pk)
    else:
        messages.warning(
            request, 
            f'Insufficient balance. You need ₦{course.price} but have ₦{user_balance}. Please add money to your account.'
        )
        return redirect('add_money')


def course_purchase_confirm(request, pk):
    """Show course purchase confirmation page."""
    course = get_object_or_404(Course, pk=pk, status='approved')
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if user is the course instructor
    if course.instructor == request.user:
        messages.error(request, 'You cannot purchase your own course.')
        return redirect('course_detail', pk=pk)
    
    # Check if already purchased
    if CoursePurchase.objects.filter(course=course, buyer=request.user).exists():
        messages.info(request, 'You have already purchased this course.')
        return redirect('course_detail', pk=pk)
    
    user_balance = get_user_balance(request.user)
    
    if not can_afford_purchase(request.user, course.price):
        messages.error(request, 'Insufficient balance.')
        return redirect('add_money')
    
    if request.method == 'POST':
        # Process the purchase
        admin_fee = course.price * 0.05  # 5% admin fee
        
        # Create purchase record
        purchase = CoursePurchase.objects.create(
            course=course,
            buyer=request.user,
            seller=course.instructor,
            purchase_price=course.price,
            admin_fee=admin_fee,
            status='completed'
        )
        
        # Create transactions
        create_purchase_transaction(
            user=request.user,
            amount=course.price,
            description=f"Purchase of course: {course.title}",
            reference=f"course_purchase_{purchase.id}"
        )
        
        create_sale_transaction(
            user=course.instructor,
            amount=course.price,
            description=f"Sale of course: {course.title}",
            reference=f"course_sale_{purchase.id}",
            admin_fee=admin_fee
        )
        
        messages.success(request, f'✅ Successfully purchased "{course.title}"!')
        return redirect('course_purchases')
    
    context = {
        'course': course,
        'user_balance': user_balance,
        'admin_fee': course.price * 0.05,
        'net_amount': course.price - (course.price * 0.05)
    }
    
    return render(request, 'courses/purchase_confirm.html', context)


@login_required
def course_purchases(request):
    """Show user's course purchases."""
    purchases = CoursePurchase.objects.filter(buyer=request.user).order_by('-purchased_at')
    
    context = {
        'purchases': purchases,
        'title': 'My Course Purchases'
    }
    
    return render(request, 'courses/purchases.html', context)


@login_required
def course_sales(request):
    """Show user's course sales."""
    sales = CoursePurchase.objects.filter(seller=request.user).order_by('-purchased_at')
    
    context = {
        'sales': sales,
        'title': 'My Course Sales'
    }
    
    return render(request, 'courses/sales.html', context)