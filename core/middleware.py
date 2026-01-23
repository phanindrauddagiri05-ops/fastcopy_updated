from django.shortcuts import redirect, render
from django.urls import reverse
from django.conf import settings
from .models import MaintenanceSettings

class MaintenanceMiddleware:
    """
    Middleware to intercept all requests and redirect to maintenance page
    if Maintenance Mode is enabled.
    
    Exemptions:
    - Admin site (/admin/)
    - Static and Media files
    - Maintenance page itself
    - Staff/Superusers
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow static and media files requests to pass through always
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # Allow admin site access
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            # Check maintenance settings
            maintenance_settings = MaintenanceSettings.get_settings()
            
            if maintenance_settings.is_enabled:
                # If user is staff/superuser, allow access
                if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
                    return self.get_response(request)
                    
                # Prevent redirect loop
                if request.path == reverse('maintenance'):
                    return self.get_response(request)
                    
                # Redirect to maintenance page
                return redirect('maintenance')
                
            else:
                # If maintenance is disabled, but user tries to access /maintenance/, redirect to home
                if request.path == reverse('maintenance'):
                    return redirect('home')

        except Exception as e:
            # Fallback if DB not ready or other error
            print(f"Maintenance Middleware Error: {e}")
            pass

        return self.get_response(request)
