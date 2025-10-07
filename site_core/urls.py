from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    
    # Category Management
    path('categories/', views.category_management, name='category_management'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    
    # Financial Management
    path('financial/', views.financial_management, name='financial_management'),
    path('transactions/<int:transaction_id>/<str:action>/', views.process_transaction, name='process_transaction'),
    path('notifications/toggle/<int:notification_id>/', views.toggle_notification, name='toggle_notification'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    


    
    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics'),
    
    # Notifications
    path('notifications/', views.notification_management, name='notification_management'),
    
    # Settings
    path('settings/', views.site_settings, name='site_settings'),
    
    # Moderation
    path('moderation/', views.moderation_panel, name='moderation_panel'),
    path('kyc/', views.kyc_management, name='kyc_management'),
    path('kyc/<int:kyc_id>/', views.kyc_detail, name='kyc_detail'),
    
    
    path('financial/manual-deposit/<int:deposit_id>/', views.manual_deposit_detail, name='manual_deposit_detail'), # <-- New
    path('settings/payment/', views.payment_settings, name='payment_settings'),
    path('settings/payment/toggle/<int:method_id>/', views.toggle_payment_method, name='toggle_payment_method'),


]