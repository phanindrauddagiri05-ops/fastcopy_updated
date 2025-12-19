import PyPDF2
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Service, Order, Profile

# --- Static Content Views ---
def home(request):
    services = Service.objects.all()
    return render(request, 'core/index.html', {'services': services})

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

# --- Services Page with Separate Forms Logic ---
def services_page(request):
    services = Service.objects.all()
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.warning(request, "Please login to place an order.")
            return redirect('login')
        
        # Capture form data based on service context
        Order.objects.create(
            user=request.user,
            service_name=request.POST.get('service_name'),
            document=request.FILES.get('document'),
            print_type=request.POST.get('print_type', 'N/A'),
            side_type=request.POST.get('side_type', 'N/A'),
            copies=int(request.POST.get('copies', 1)),
            total_price=int(request.POST.get('total_price_hidden', 0))
        )
        messages.success(request, "Order placed successfully!")
        return redirect('profile')
    return render(request, 'core/services.html', {'services': services})

# --- AJAX APIs (PDF & Cart) ---
@csrf_exempt
def calculate_pages(request):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            reader = PyPDF2.PdfReader(request.FILES['document'])
            return JsonResponse({'success': True, 'pages': len(reader.pages)})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        item = {
            'service_name': request.POST.get('service_name'),
            'total_price': int(request.POST.get('total_price_hidden', 0)),
            'copies': request.POST.get('copies', 1)
        }
        cart = request.session.get('cart', [])
        cart.append(item)
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'success': True, 'cart_count': len(cart)})
    return JsonResponse({'success': False})


def cart(request):
    cart_items = request.session.get('cart', [])
    total = sum(int(i['total_price']) for i in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total': total})
def clear_cart(request): # Restored missing clear_cart view
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('cart')

# --- Authentication & Profile ---
def login_view(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get('mobile'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('profile')
        messages.error(request, "Invalid login credentials.")
    return render(request, 'core/login.html')

def register_view(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        user = User.objects.create_user(username=mobile, password=request.POST.get('password'), first_name=request.POST.get('username'))
        Profile.objects.create(user=user, mobile=mobile, address=request.POST.get('address'))
        return redirect('login')
    return render(request, 'core/register.html')

def profile_view(request):
    if not request.user.is_authenticated: return redirect('login')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/profile.html', {'orders': orders})

def logout_view(request):
    logout(request)
    return redirect('home')