from django.urls import path
from . import views

urlpatterns = [
    path('add-money/', views.add_money, name='add_money'),
    path('withdraw/', views.withdraw_money, name='withdraw_money'),
    path('transfer/', views.transfer_money, name='transfer_money'),
    path('manual-deposit/', views.manual_deposit, name='manual_deposit'),
    path('manual-deposits/', views.manual_deposit_list, name='manual_deposit_list'),
]