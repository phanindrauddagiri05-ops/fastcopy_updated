import PyPDF2
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Service, Order, UserProfile

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

# --- AUTHENTICATION (MOBILE BASED) ---
def register_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        address = request.POST.get('address')
        pw = request.POST.get('password')
        cpw = request.POST.get('confirm_password')

        if pw != cpw:
            messages.error(request, "Passwords do not match!")
            return redirect('register')
        
        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Mobile number already registered!")
            return redirect('register')

        user = User.objects.create_user(username=mobile, email=email, password=pw, first_name=name)
        UserProfile.objects.create(user=user, mobile=mobile, address=address)
        return redirect('login')
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        pw = request.POST.get('password')
        user = authenticate(request, username=mobile, password=pw)
        if user:
            login(request, user)
            return redirect('profile')
        messages.error(request, "Invalid Credentials")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# --- PROFILE & HISTORY ---
@login_required(login_url='login')
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'mobile': request.user.username, 'address': 'Not Provided'}
    )
    all_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/profile.html', {
        'profile': user_profile,
        'recent_bookings': all_orders[:3],
        'tracking': all_orders.exclude(status='Delivered').first(),
        'all_orders_count': all_orders.count()
    })

@login_required(login_url='login')
def history_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'core/history.html', {'orders': orders, 'profile': profile})

# --- CART LOGIC (FIXED NAMES) ---
def cart_page(request): # Changed from 'cart' to 'cart_page' to match your URL
    cart_items = request.session.get('cart', [])
    total_bill = sum(int(item.get('total_price', 0)) for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total_bill': total_bill})

def remove_from_cart(request, item_id):
    cart_list = request.session.get('cart', [])
    if 0 <= item_id < len(cart_list):
        cart_list.pop(item_id)
        request.session['cart'] = cart_list
        request.session.modified = True
    return redirect('cart')

# --- ORDERING ---
@login_required(login_url='login')
def order_now(request):
    if request.method == "POST":
        Order.objects.create(
            user=request.user,
            service_name=request.POST.get('service_name'),
            file_name=request.FILES.get('document').name if request.FILES.get('document') else "Direct",
            total_price=request.POST.get('total_price_hidden'),
        )
        return redirect('profile')
    return redirect('services')

@login_required(login_url='login')
def process_cart_order(request):
    cart_items = request.session.get('cart', [])
    for item in cart_items:
        Order.objects.create(
            user=request.user, service_name=item['service_name'],
            total_price=item['total_price'], status='In Progress'
        )
    request.session['cart'] = []
    request.session.modified = True
    return redirect('profile')

# --- AJAX ---
def calculate_pages(request):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            pdf = PyPDF2.PdfReader(request.FILES['document'])
            return JsonResponse({'success': True, 'pages': len(pdf.pages)})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def add_to_cart(request):
    if request.method == "POST":
        item = {
            'service_name': request.POST.get('service_name'),
            'total_price': request.POST.get('total_price_hidden'),
            'file_name': request.FILES.get('document').name if request.FILES.get('document') else "Manual",
        }
        cart = request.session.get('cart', [])
        cart.append(item)
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'success': True, 'cart_count': len(cart)})
    return JsonResponse({'success': False})