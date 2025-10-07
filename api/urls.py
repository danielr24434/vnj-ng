from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.JobViewSet, basename='job')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'affiliate-sales', views.AffiliateSaleViewSet, basename='affiliate-sale')
router.register(r'blog-posts', views.BlogPostViewSet, basename='blog-post')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]