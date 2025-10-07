from django.contrib import admin
from .models import ProductCategory, Product, ProductSale

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'product_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'license_type', 'price', 'status', 'views_count', 'download_count', 'created_at')
    list_filter = ('status', 'license_type', 'category', 'created_at')
    search_fields = ('title', 'description', 'seller__username')
    readonly_fields = ('created_at', 'updated_at', 'views_count', 'download_count')
    actions = ['approve_products', 'reject_products']
    
    
    def approve_products(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} products approved successfully.')
    approve_products.short_description = "Approve selected products"
    
    def reject_products(self, request, queryset):
        for product in queryset:
            product.status = 'rejected'
            product.save()
        self.message_user(request, f'{queryset.count()} products rejected.')
    reject_products.short_description = "Reject selected products"

@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'buyer', 'seller', 'sale_price', 'commission_amount', 'net_amount', 'status', 'purchased_at')
    list_filter = ('status', 'purchased_at')
    search_fields = ('product__title', 'buyer__username', 'seller__username')
    readonly_fields = ('purchased_at', 'license_key')
    
    
    
    
    