from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from accounts.models import User
from jobs.models import Job
from courses.models import Course
from products.models import Product
from payments.models import Transaction
from affiliates.models import AffiliateSale
from blog.models import BlogPost
from .serializers import (
    UserSerializer, JobSerializer, CourseSerializer, ProductSerializer,
    TransactionSerializer, AffiliateSaleSerializer, BlogPostSerializer
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(status='approved').select_related('posted_by', 'category')
    serializer_class = JobSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'job_type', 'level_requirement']
    search_fields = ['title', 'description', 'company_name']
    ordering_fields = ['created_at', 'price', 'salary_min']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user, status='pending')

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(status='approved').select_related('instructor', 'category')
    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'level', 'mode']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'start_date']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user, status='pending')

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(status='approved').select_related('seller', 'category')
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'license_type']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user, status='pending')

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['transaction_type', 'status']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

class AffiliateSaleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AffiliateSaleSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return AffiliateSale.objects.filter(referral__referrer=self.request.user)

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.filter(status='published').select_related('author', 'category')
    serializer_class = BlogPostSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['created_at', 'views_count']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status='pending')