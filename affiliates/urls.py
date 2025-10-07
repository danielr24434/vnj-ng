from django.urls import path
from . import views

urlpatterns = [
    path('', views.affiliate_dashboard, name='affiliate_dashboard'),
    path('referrals/', views.referral_list, name='referral_list'),
]