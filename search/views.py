from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from jobs.models import Job
from courses.models import Course
from products.models import Product
from blog.models import BlogPost

def search_results(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', 'all')
    
    results = {
        'jobs': [],
        'courses': [],
        'products': [],
        'blog_posts': [],
    }
    
    if query:
        if category in ['all', 'jobs']:
            results['jobs'] = Job.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company_name__icontains=query),
                status='approved'
            ).select_related('posted_by', 'category')[:10]
        
        if category in ['all', 'courses']:
            results['courses'] = Course.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query),
                status='approved'
            ).select_related('instructor', 'category')[:10]
        
        if category in ['all', 'products']:
            results['products'] = Product.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query),
                status='approved'
            ).select_related('seller', 'category')[:10]
        
        if category in ['all', 'blog']:
            results['blog_posts'] = BlogPost.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query),
                status='published'
            ).select_related('author', 'category')[:10]
    
    total_results = sum(len(items) for items in results.values())
    
    context = {
        'query': query,
        'category': category,
        'results': results,
        'total_results': total_results,
    }
    
    return render(request, 'search/results.html', context)