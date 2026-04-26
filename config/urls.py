"""
Root URL configuration for Alanaatii Backend
All routes are prefixed with /api/v1/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Django admin
    path('django-admin/', admin.site.urls),

    # OpenAPI Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # App routes
    path('api/v1/', include([
        path('', include('apps.accounts.urls')),
        path('', include('apps.catalog.urls')),
        path('', include('apps.orders.urls')),
        path('', include('apps.writers.urls')),
        path('', include('apps.admin_ops.urls')),
        path('', include('apps.notifications.urls')),
        path('', include('apps.content.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
