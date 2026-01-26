import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
django.setup()

from django.contrib.sites.models import Site

# Get the current site (default ID usually 1)
site = Site.objects.get(pk=1)

print(f"Current Site Configuration: Domain={site.domain}, Name={site.name}")

# Update to match local development
site.domain = 'localhost:8000'
site.name = 'FastCopy Local'
site.save()

print(f"Updated Site Configuration: Domain={site.domain}, Name={site.name}")
print("Site updated successfully. This should fix the redirect_uri mismatch.")
