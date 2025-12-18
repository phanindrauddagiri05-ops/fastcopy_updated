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
def cart(request):
    # Logic: In a real scenario, we would fetch this from the session or database
    # For now, let's assume an empty list to test the 'Empty' state
    cart_items = [] 
    return render(request, 'core/cart.html', {'cart_items': cart_items})