from django.shortcuts import render

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import BlogPost, BlogComment, Category, Tag, SavedArticle
from .forms import BlogPostForm, BlogCommentForm
from django.contrib.auth.decorators import login_required

class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = BlogPost.objects.filter(status='published').select_related('author', 'category')
        
        category_slug = self.request.GET.get('category')
        tag_slug = self.request.GET.get('tag')
        search = self.request.GET.get('search')
        
        if category_slug:
            queryset = queryset.filter(category__name__iexact=category_slug)
        if tag_slug:
            queryset = queryset.filter(tags__name__iexact=tag_slug)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(excerpt__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['popular_tags'] = Tag.objects.annotate(
            post_count=Count('posts')
        ).filter(post_count__gt=0).order_by('-post_count')[:10]
        return context

class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return BlogPost.objects.select_related('author', 'category').prefetch_related('tags', 'comments')
    
    def get_object(self):
        obj = super().get_object()
        if obj.status == 'published':
            obj.increment_views()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = BlogCommentForm()
        context['comments'] = self.object.comments.filter(is_approved=True).select_related('author')
        
        if self.request.user.is_authenticated:
            context['is_saved'] = SavedArticle.objects.filter(
                user=self.request.user, 
                post=self.object
            ).exists()
        
        return context

class BlogPostCreateView(LoginRequiredMixin, CreateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog_list')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class BlogPostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/edit.html'
    
    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('blog_detail', kwargs={'slug': self.object.slug})

@login_required
def add_comment(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    
    if request.method == 'POST':
        form = BlogCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    
    return redirect('blog_detail', slug=slug)

@login_required
def save_article(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    saved_article, created = SavedArticle.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        saved_article.delete()
    
    return redirect('blog_detail', slug=slug)

@login_required
def manage_posts(request):
    posts = BlogPost.objects.filter(author=request.user).select_related('category')
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'posts': page_obj,
    }
    return render(request, 'blog/manage.html', context)