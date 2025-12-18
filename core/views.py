from django.shortcuts import render
from .models import Service

def home(request):
    services = Service.objects.all()
    return render(request, 'core/index.html', {'services': services})

def services_page(request):
    services = Service.objects.all()
    return render(request, 'core/services.html', {'services': services})
def about(request):
    return render(request, 'core/about.html')
def contact(request):
    return render(request, 'core/contact.html')