from django.urls import path
from . import views

urlpatterns = [
    path('', views.BlogPostListView.as_view(), name='blog_list'),
    path('<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog_detail'),
    path('create/', views.BlogPostCreateView.as_view(), name='blog_create'),
    path('<slug:slug>/edit/', views.BlogPostUpdateView.as_view(), name='blog_edit'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('<slug:slug>/save/', views.save_article, name='save_article'),
    path('manage/', views.manage_posts, name='blog_manage'),
]