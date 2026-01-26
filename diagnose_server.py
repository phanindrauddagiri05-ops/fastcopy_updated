import os
import sys
import django

print("--- FASTCOPY SERVER DIAGNOSTIC TOOL ---")

# 1. Check Environment
print(f"Python Version: {sys.version}")
try:
    import allauth
    print(f"Allauth Version: {allauth.__version__}")
except ImportError:
    print("❌ CRITICAL: django-allauth is NOT installed.")

# 2. Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
try:
    django.setup()
    print("✅ Django Setup Successful")
except Exception as e:
    print(f"❌ Django Setup Failed: {e}")
    sys.exit(1)

from django.conf import settings
from django.contrib.sites.models import Site

# 3. Check SITE_ID and Domain
print(f"SITE_ID in settings: {getattr(settings, 'SITE_ID', 'Not Set')}")
try:
    current_site = Site.objects.get(pk=settings.SITE_ID)
    print(f"✅ Current Site (DB): ID={current_site.id}, Domain='{current_site.domain}', Name='{current_site.name}'")
except Exception as e:
    print(f"❌ Site Error: {e}")
    
# 4. Check Environment Variables (Crucial for Google Login)
client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

if client_id:
    print(f"✅ GOOGLE_CLIENT_ID: Found (Starts with: {client_id[:5]}...)")
else:
    print("❌ GOOGLE_CLIENT_ID: MISSING or Empty")

if client_secret:
    print(f"✅ GOOGLE_CLIENT_SECRET: Found")
else:
    print("❌ GOOGLE_CLIENT_SECRET: MISSING or Empty")
    
# 5. Check Database Tables
try:
    from allauth.socialaccount.models import SocialApp, SocialAccount
    app_count = SocialApp.objects.count()
    print(f"SocialApps in DB: {app_count} (Note: We use settings-based config, so 0 is okay usually, but check if code expects DB)")
except Exception as e:
    print(f"❌ Database Error (Migrations missing?): {e}")

print("--- END DIAGNOSIS ---")
