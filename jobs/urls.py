from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListView.as_view(), name='jobs_list'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('create/', views.JobCreateView.as_view(), name='job_create'),
    path('<int:pk>/edit/', views.JobUpdateView.as_view(), name='job_edit'),
    path('<int:pk>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    path('manage/', views.JobManageView.as_view(), name='job_manage'),
    path('<int:pk>/approve/', views.approve_job, name='approve_job'),
    path('<int:pk>/reject/', views.reject_job, name='reject_job'),
    
    # Purchase URLs
    path('<int:pk>/purchase/', views.job_purchase_check, name='job_purchase'),
    path('<int:pk>/purchase/confirm/', views.job_purchase_confirm, name='job_purchase_confirm'),
    path('purchases/', views.job_purchases, name='job_purchases'),
    path('sales/', views.job_sales, name='job_sales'),
]