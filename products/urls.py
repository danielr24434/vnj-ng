from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProductListView.as_view(), name='products_list'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('manage/', views.ProductManageView.as_view(), name='product_manage'),
    path('<int:pk>/approve/', views.approve_product, name='approve_product'),
    path('<int:pk>/reject/', views.reject_product, name='reject_product'),
]