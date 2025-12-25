from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.admin import admin_site  # Import your custom admin site instance

urlpatterns = [
    # Custom Admin Site
    path('admin/', admin_site.urls),
    
    # Core App Routes
    path('', include('core.urls')),
]

# CRITICAL: This allows Django to serve uploaded images and PDFs during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)