from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Category, Tag, BlogPost, BlogComment, SavedArticle

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'post_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('name', 'description')
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'post_count', 'created_at')
    search_fields = ('name',)
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'views_count', 'created_at', 'published_at')
    list_filter = ('status', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'published_at')
    prepopulated_fields = {'slug': ('title',)}
    actions = ['publish_posts', 'reject_posts', 'feature_posts']
    
    def publish_posts(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} posts published.')
    publish_posts.short_description = "Publish selected posts"
    
    def reject_posts(self, request, queryset):
        for post in queryset:
            post.status = 'rejected'
            post.save()
        self.message_user(request, f'{queryset.count()} posts rejected.')
    reject_posts.short_description = "Reject selected posts"
    
    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts marked as featured.')
    feature_posts.short_description = "Mark selected posts as featured"

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'content_preview', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('post__title', 'author__username', 'content')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_comments', 'disapprove_comments']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments disapproved.')
    disapprove_comments.short_description = "Disapprove selected comments"

@admin.register(SavedArticle)
class SavedArticleAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('saved_at',)