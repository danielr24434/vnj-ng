from rest_framework import serializers
from accounts.models import User, UserProfile
from jobs.models import Job, JobCategory
from courses.models import Course, CourseCategory, Enrollment
from products.models import Product, ProductCategory, ProductSale
from affiliates.models import Referral, AffiliateSale
from payments.models import Transaction
from blog.models import BlogPost, Category, BlogComment

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'country', 'phone_number', 'date_joined']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'subscription_level', 'profile']

class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description']

class JobSerializer(serializers.ModelSerializer):
    posted_by = UserSerializer(read_only=True)
    category = JobCategorySerializer(read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'category', 'job_type', 'location',
            'company_name', 'salary_min', 'salary_max', 'deadline', 'spots_total',
            'spots_left', 'level_requirement', 'price', 'posted_by', 'status',
            'views_count', 'created_at'
        ]
        read_only_fields = ['posted_by', 'status', 'views_count', 'created_at']

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'description']

class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'category', 'level', 'instructor',
            'duration', 'mode', 'start_date', 'is_self_paced', 'price',
            'spots_total', 'spots_left', 'preview_video', 'thumbnail', 'status',
            'created_at'
        ]
        read_only_fields = ['instructor', 'status', 'created_at']

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'category', 'seller', 'license_type',
            'version', 'price', 'product_file', 'sample_file', 'thumbnail',
            'status', 'views_count', 'download_count', 'created_at'
        ]
        read_only_fields = ['seller', 'status', 'views_count', 'download_count', 'created_at']

class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'transaction_type', 'amount', 'currency', 'status',
            'payment_method', 'reference', 'description', 'metadata',
            'rejection_reason', 'created_at', 'completed_at'
        ]
        read_only_fields = ['user', 'reference', 'created_at', 'completed_at']

class AffiliateSaleSerializer(serializers.ModelSerializer):
    referral = serializers.StringRelatedField()
    
    class Meta:
        model = AffiliateSale
        fields = [
            'id', 'referral', 'commission_amount', 'commission_rate', 'status',
            'created_at', 'paid_at'
        ]

class BlogPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = serializers.StringRelatedField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'author', 'category',
            'featured_image', 'status', 'is_featured', 'views_count', 'created_at',
            'published_at'
        ]
        read_only_fields = ['author', 'slug', 'views_count', 'created_at', 'published_at']