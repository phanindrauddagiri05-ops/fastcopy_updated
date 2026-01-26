import os
import django
import sys

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
django.setup()

from django.contrib.sites.models import Site
from django.conf import settings

def update_site():
    print("--- UPDATING SITE CONFIGURATION ---")
    
    # Get the current site ID (should be 1)
    site_id = getattr(settings, 'SITE_ID', 1)
    
    try:
        site = Site.objects.get(pk=site_id)
        print(f"Current Site: {site.domain} ({site.name})")
        
        # Update to Production Domain
        domain = "fastcopies.in" 
        name = "FastCopies"
        
        if site.domain != domain:
            print(f"Updating to: {domain}")
            site.domain = domain
            site.name = name
            site.save()
            print("✅ Site Updated Successfully!")
        else:
            print("✅ Site is already configured correctly.")
            
    except Site.DoesNotExist:
        print(f"⚠️ Site with ID {site_id} not found. Creating it...")
        Site.objects.create(pk=site_id, domain="fastcopies.in", name="FastCopies")
        print("✅ Site Created Successfully!")
        
    except Exception as e:
        print(f"❌ Error updating site: {e}")
        print("Did you run 'python manage.py migrate' first?")

if __name__ == "__main__":
    update_site()
