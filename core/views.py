import PyPDF2
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Service, Order  # Remove UserProfile from here

# --- NAVIGATION ---
def home(request):
    services = Service.objects.all()[:3]
    return render(request, 'core/index.html', {'services': services})

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

def services_page(request):
    services = Service.objects.all()
    first_service = services.first()
    return render(request, 'core/services.html', {'services': services, 'first_service': first_service})

# --- AUTHENTICATION ---
def register_view(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        pw = request.POST.get('password')
        User.objects.create_user(username=mobile, password=pw)
        messages.success(request, "Account created! Please login.")
        return redirect('login')
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        pw = request.POST.get('password')
        user = authenticate(request, username=mobile, password=pw)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, "Invalid Credentials")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# --- CART & ORDERING ---
def cart_page(request):
    cart_items = request.session.get('cart', [])
    total_bill = sum(int(item.get('total_price', 0)) for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total_bill': total_bill})

@login_required(login_url='login')
def order_now(request):
    if request.method == "POST":
        Order.objects.create(
            user=request.user,
            service_name=request.POST.get('service_name'),
            total_price=request.POST.get('total_price_hidden', 0),
        )
        messages.success(request, "Order placed successfully!")
        return redirect('home')
    return redirect('services')

@login_required(login_url='login')
def order_all(request):
    cart_items = request.session.get('cart', [])
    for item in cart_items:
        Order.objects.create(
            user=request.user,
            service_name=item['service_name'],
            total_price=item['total_price']
        )
    request.session['cart'] = []
    request.session.modified = True
    messages.success(request, "All items ordered successfully!")
    return redirect('home')

# --- AJAX ---
def calculate_pages(request):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            pdf = PyPDF2.PdfReader(request.FILES['document'])
            return JsonResponse({'success': True, 'pages': len(pdf.pages)})
        except: return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def add_to_cart(request):
    if request.method == "POST":
        item = {
            'service_name': request.POST.get('service_name'),
            'total_price': request.POST.get('total_price_hidden'),
        }
        cart = request.session.get('cart', [])
        cart.append(item)
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'success': True, 'cart_count': len(cart)})
    return JsonResponse({'success': False})

def remove_from_cart(request, item_id):
    cart = request.session.get('cart', [])
    if 0 <= item_id < len(cart):
        cart.pop(item_id)
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')