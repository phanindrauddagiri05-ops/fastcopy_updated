from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from core.admin import admin_site  # Import your custom admin instance
import os

# Serve sitemap.xml
def serve_sitemap(request):
    sitemap_path = os.path.join(settings.BASE_DIR, 'sitemap.xml')
    with open(sitemap_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='application/xml')

# Serve robots.txt
def serve_robots(request):
    robots_path = os.path.join(settings.BASE_DIR, 'robots.txt')
    with open(robots_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/plain')

urlpatterns = [
    # 🛠️ Custom Admin Site
    path('admin/', admin_site.urls),
    
    # 🤖 SEO Files
    path('sitemap.xml', serve_sitemap, name='sitemap'),
    path('robots.txt', serve_robots, name='robots'),
    
    # 🏠 Core App URLs
    path('', include('core.urls')),
]

# 📂 Serve Media Files (PDFs/Images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)