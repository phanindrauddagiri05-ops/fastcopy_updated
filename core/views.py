import PyPDF2
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Service, Profile, Order

# --- 1. HOME & STATIC ---
def home(request):
    services = Service.objects.all()
    return render(request, 'core/index.html', {'services': services})

def about(request): return render(request, 'core/about.html')
def contact(request): return render(request, 'core/contact.html')

# --- 2. SERVICES & PDF CALCULATION ---
def services_page(request):
    services = Service.objects.all()
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please login to place an order.")
            return redirect('login')
            
        Order.objects.create(
            user=request.user,
            service_name=request.POST.get('service_name'),
            document=request.FILES.get('document'),
            print_type=request.POST.get('print_type'),
            side_type=request.POST.get('side_type'),
            copies=int(request.POST.get('copies', 1)),
            total_price=int(request.POST.get('total_price_hidden', 0))
        )
        messages.success(request, "Order placed successfully!")
        return redirect('profile')
    return render(request, 'core/services.html', {'services': services})

@csrf_exempt
def calculate_pages(request):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            reader = PyPDF2.PdfReader(request.FILES['document'])
            return JsonResponse({'success': True, 'pages': len(reader.pages)})
        except:
            return JsonResponse({'success': False, 'error': 'Invalid PDF'})
    return JsonResponse({'success': False})

# --- 3. CART LOGIC (SESSIONS) ---
def cart(request):
    cart_items = request.session.get('cart', [])
    total_bill = sum(item['total_price'] for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total_bill': total_bill})

@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        item = {
            'service_name': request.POST.get('service_name'),
            'print_type': request.POST.get('print_type'),
            'side_type': request.POST.get('side_type'),
            'copies': request.POST.get('copies'),
            'total_price': int(request.POST.get('total_price_hidden', 0)),
        }
        cart_data = request.session.get('cart', [])
        cart_data.append(item)
        request.session['cart'] = cart_data
        return JsonResponse({'success': True, 'cart_count': len(cart_data)})
    return JsonResponse({'success': False})

# --- 4. AUTH & PROFILE ---
def login_view(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get('mobile'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('profile')
        messages.error(request, "Invalid credentials.")
    return render(request, 'core/login.html')

def register_view(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Mobile already registered.")
            return redirect('register')
        user = User.objects.create_user(username=mobile, password=request.POST.get('password'), first_name=request.POST.get('username'))
        Profile.objects.create(user=user, mobile=mobile, address=request.POST.get('address'))
        return redirect('login')
    return render(request, 'core/register.html')

def profile_view(request):
    if not request.user.is_authenticated: return redirect('login')
    profile = Profile.objects.get(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'core/profile.html', {'profile': profile, 'orders': orders})

def logout_view(request):
    logout(request)
    return redirect('home')