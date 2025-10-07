from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from payments.webhooks import monnify_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('courses/', include('courses.urls')),
    path('products/', include('products.urls')),
    path('affiliates/', include('affiliates.urls')),
    path('mentorship/', include('mentorship.urls')),
    path('payments/', include('payments.urls')),
    path('pricing/', include('pricing.urls')),
    path('transactions/', include('transactions.urls')),
    path('blog/', include('blog.urls')),
    path('search/', include('search.urls')),
    path('site-admin/', include('site_core.urls')),
    path('api/', include('api.urls')),
    path('webhooks/monnify/', monnify_webhook, name='monnify_webhook'),
    

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])   
