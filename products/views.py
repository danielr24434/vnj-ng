from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Product, ProductSale
from .forms import ProductForm
from site_core.models import Category

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Product

@require_POST
@login_required
def approve_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.status = 'approved'
    product.save()
    messages.success(request, f"✅ '{product.title}' has been approved successfully.")
    return redirect('product_manage')


@require_POST
@login_required
def reject_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.status = 'rejected'
    product.save()
    messages.error(request, f"❌ '{product.title}' has been rejected.")
    return redirect('product_manage')




class ProductManageView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/manage.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).select_related('category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.get_queryset()
        
        context.update({
            'approved_products': products.filter(status='approved').count(),
            'pending_products': products.filter(status='pending').count(),
            'rejected_products': products.filter(status='rejected').count(),
        })
        return context
    
    
    
class ProductListView(ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(status='approved').select_related('seller', 'category')
        
        category = self.request.GET.get('category')
        license_type = self.request.GET.get('license_type')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__name=category)
        if license_type:
            queryset = queryset.filter(license_type=license_type)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(category_type="job", is_active=True)
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        obj = super().get_object()
        obj.increment_views()
        return obj

from django.contrib import messages
from django.urls import reverse_lazy

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/create.html'
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        form.instance.status = 'pending'
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            '✅ Your product has been submitted for admin approval. You will be notified once approved.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Please correct the errors below.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('products_list')

class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/edit.html'
    success_url = reverse_lazy('products_list')
    
    def test_func(self):
        product = self.get_object()
        return product.seller == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, '✅ Product updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '❌ Please correct the errors below.')
        return super().form_invalid(form)

class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'products/delete.html'
    success_url = reverse_lazy('product_manage')
    
    def test_func(self):
        product = self.get_object()
        return product.seller == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '✅ Product deleted successfully!')
        return super().delete(request, *args, **kwargs)