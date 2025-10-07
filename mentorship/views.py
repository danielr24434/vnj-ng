from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from .models import MentorshipOffer, MentorshipApplication, Mentor, MentorshipEnrollment, MentorshipChat
from .forms import MentorshipOfferForm, MentorshipApplicationForm
from payments.models import Transaction
from site_core.models import SiteSetting
from transactions.utils import get_user_balance, can_afford_purchase, create_purchase_transaction, create_sale_transaction

User = get_user_model()

class MentorshipOfferListView(ListView):
    model = MentorshipOffer
    template_name = 'mentorship/list.html'
    context_object_name = 'offers'
    paginate_by = 20
    
    def get_queryset(self):
        return MentorshipOffer.objects.filter(
            status='approved', 
            is_available=True
        ).select_related('mentor')

class MentorshipOfferDetailView(DetailView):
    model = MentorshipOffer
    template_name = 'mentorship/detail.html'
    context_object_name = 'offer'

class MentorshipOfferCreateView(LoginRequiredMixin, CreateView):
    model = MentorshipOffer
    form_class = MentorshipOfferForm
    template_name = 'mentorship/create.html'
    success_url = reverse_lazy('mentorship_list')
    
    def form_valid(self, form):
        form.instance.mentor = self.request.user
        form.instance.status = 'pending'
        return super().form_valid(form)

class MentorshipApplicationCreateView(LoginRequiredMixin, CreateView):
    model = MentorshipApplication
    form_class = MentorshipApplicationForm
    template_name = 'mentorship/apply.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.mentorship_offer = get_object_or_404(MentorshipOffer, pk=self.kwargs['offer_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentorship_offer'] = self.mentorship_offer
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            form.instance.mentorship_offer = self.mentorship_offer
            form.instance.applicant = self.request.user
            
            site_settings = SiteSetting.get_solo()
            total_amount = form.instance.total_amount
            admin_fee = total_amount * (site_settings.mentorship_fee_pct / 100)
            net_amount = total_amount - admin_fee
            
            response = super().form_valid(form)
            
            Transaction.objects.create(
                user=self.request.user,
                amount=total_amount,
                transaction_type='MENTORSHIP_PAYMENT',
                status='pending',
                description=f"Mentorship application for {self.mentorship_offer.title}",
                metadata={
                    'mentorship_application_id': form.instance.id,
                    'mentor_id': self.mentorship_offer.mentor.id,
                    'admin_fee': float(admin_fee),
                    'net_amount': float(net_amount),
                }
            )
            
            return response
    
    def get_success_url(self):
        return reverse_lazy('mentorship_application_detail', kwargs={'pk': self.object.pk})

@login_required
def manage_mentorship(request):
    user = request.user
    
    if request.user.subscription_level == 'mentorship':
        offers = MentorshipOffer.objects.filter(mentor=user)
        applications = MentorshipApplication.objects.filter(mentorship_offer__mentor=user)
    else:
        offers = MentorshipOffer.objects.none()
        applications = MentorshipApplication.objects.filter(applicant=user)
    
    context = {
        'offers': offers,
        'applications': applications,
    }
    
    return render(request, 'mentorship/manage.html', context)


# New Mentor Management System Views
def available_mentors(request):
    """Display available mentors for enrollment"""
    mentors = Mentor.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'mentors': mentors,
        'title': 'Available Mentors'
    }
    
    return render(request, 'mentorship/available_mentors.html', context)


def mentor_enroll_check(request, pk):
    """Check if user can afford the mentor and redirect accordingly."""
    mentor = get_object_or_404(Mentor, pk=pk, is_active=True)
    
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to enroll with this mentor.')
        return redirect('login')
    
    # Check if already enrolled
    if MentorshipEnrollment.objects.filter(mentor=mentor, student=request.user).exists():
        messages.info(request, 'You are already enrolled with this mentor.')
        return redirect('my_mentorships')
    
    # Check if mentor has available slots
    if not mentor.is_available:
        messages.error(request, 'This mentor is not available or has no slots left.')
        return redirect('available_mentors')
    
    user_balance = get_user_balance(request.user)
    
    if can_afford_purchase(request.user, mentor.price):
        return redirect('mentor_enroll_confirm', pk=pk)
    else:
        messages.warning(
            request, 
            f'Insufficient balance. You need ₦{mentor.price} but have ₦{user_balance}. Please add money to your account.'
        )
        return redirect('add_money')


def mentor_enroll_confirm(request, pk):
    """Show mentor enrollment confirmation page."""
    mentor = get_object_or_404(Mentor, pk=pk, is_active=True)
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if already enrolled
    if MentorshipEnrollment.objects.filter(mentor=mentor, student=request.user).exists():
        messages.info(request, 'You are already enrolled with this mentor.')
        return redirect('my_mentorships')
    
    # Check if mentor has available slots
    if not mentor.is_available:
        messages.error(request, 'This mentor is not available or has no slots left.')
        return redirect('available_mentors')
    
    user_balance = get_user_balance(request.user)
    
    if not can_afford_purchase(request.user, mentor.price):
        messages.error(request, 'Insufficient balance.')
        return redirect('add_money')
    
    if request.method == 'POST':
        # Process the enrollment
        admin_fee = mentor.price * 0.05  # 5% admin fee
        
        # Create enrollment record
        enrollment = MentorshipEnrollment.objects.create(
            mentor=mentor,
            student=request.user,
            purchase_price=mentor.price,
            admin_fee=admin_fee,
            status='active'
        )
        
        # Update mentor slots
        mentor.slots_taken += 1
        mentor.people_mentored_count += 1
        mentor.save()
        
        # Create transactions
        create_purchase_transaction(
            user=request.user,
            amount=mentor.price,
            description=f"Mentorship enrollment with {mentor.name}",
            reference=f"mentorship_enrollment_{enrollment.id}"
        )
        
        # Note: We don't create a sale transaction for mentors since they're not users
        # The admin will handle mentor payments separately
        
        messages.success(request, f'✅ Successfully enrolled with "{mentor.name}"! You can now start chatting.')
        return redirect('my_mentorships')
    
    context = {
        'mentor': mentor,
        'user_balance': user_balance,
        'admin_fee': mentor.price * 0.05,
    }
    
    return render(request, 'mentorship/enroll_confirm.html', context)


@login_required
def my_mentorships(request):
    """Show user's mentorship enrollments."""
    enrollments = MentorshipEnrollment.objects.filter(student=request.user).order_by('-enrolled_at')
    
    context = {
        'enrollments': enrollments,
        'title': 'My Mentorships'
    }
    
    return render(request, 'mentorship/my_mentorships.html', context)


@login_required
def mentorship_chat(request, tracking_id):
    """Chat interface for mentorship."""
    enrollment = get_object_or_404(MentorshipEnrollment, tracking_id=tracking_id)
    
    # Check if user is authorized to access this chat
    if request.user != enrollment.student:
        # Check if user is the mentor (by username)
        try:
            mentor_user = User.objects.get(username=enrollment.mentor.username)
            if request.user != mentor_user:
                messages.error(request, 'You are not authorized to access this chat.')
                return redirect('available_mentors')
        except User.DoesNotExist:
            messages.error(request, 'Mentor user not found.')
            return redirect('available_mentors')
    
    # Get chat messages
    messages_list = MentorshipChat.objects.filter(enrollment=enrollment)
    
    # Mark messages as read for the current user
    MentorshipChat.objects.filter(
        enrollment=enrollment,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        if message_text:
            MentorshipChat.objects.create(
                enrollment=enrollment,
                sender=request.user,
                message=message_text
            )
            messages.success(request, 'Message sent!')
            return redirect('mentorship_chat', tracking_id=tracking_id)
    
    context = {
        'enrollment': enrollment,
        'messages': messages_list,
        'is_mentor': request.user.username == enrollment.mentor.username,
    }
    
    return render(request, 'mentorship/chat.html', context)


@login_required
def mentor_dashboard(request):
    """Dashboard for mentors to see their students and chats."""
    try:
        mentor = Mentor.objects.get(username=request.user.username)
    except Mentor.DoesNotExist:
        messages.error(request, 'You are not registered as a mentor.')
        return redirect('available_mentors')
    
    enrollments = MentorshipEnrollment.objects.filter(mentor=mentor).order_by('-enrolled_at')
    
    context = {
        'mentor': mentor,
        'enrollments': enrollments,
        'title': 'Mentor Dashboard'
    }
    
    return render(request, 'mentorship/mentor_dashboard.html', context)