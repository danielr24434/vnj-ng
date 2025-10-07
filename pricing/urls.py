from django.urls import path
from . import views

urlpatterns = [
    path('', views.PricingListView.as_view(), name='pricing_list'),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
]