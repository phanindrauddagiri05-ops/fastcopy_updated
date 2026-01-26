import os
import django
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
django.setup()

from django.contrib.sites.models import Site

site = Site.objects.get_current()
callback_path = reverse('google_callback')
full_callback_url = f"http://{site.domain}{callback_path}"

print("\n" + "="*50)
print("CONFIGURATION CHECK")
print("="*50)
print(f"Current Site Domain:  {site.domain}")
print(f"Callback Path:        {callback_path}")
print(f"Generated Callback:   {full_callback_url}")
print("="*50)
print("\nACTION REQUIRED: Compare 'Generated Callback' with what you put in Google Console.")
print("   They must be IDENTICAL (including http vs https and trailing slashes).")
