from django.urls import path
from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='courses_list'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('manage/', views.CourseManageView.as_view(), name='course_manage'),
    path('<int:pk>/approve/', views.approve_course, name='approve_course'),
    path('<int:pk>/reject/', views.reject_course, name='reject_course'),
    
    # Purchase URLs
    path('<int:pk>/purchase/', views.course_purchase_check, name='course_purchase'),
    path('<int:pk>/purchase/confirm/', views.course_purchase_confirm, name='course_purchase_confirm'),
    path('purchases/', views.course_purchases, name='course_purchases'),
    path('sales/', views.course_sales, name='course_sales'),
]