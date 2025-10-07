from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),

    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:pk>/mark/', views.mark_notification_read, name='mark_notification_read'),
]
