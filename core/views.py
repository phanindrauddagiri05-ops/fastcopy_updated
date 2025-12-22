import PyPDF2
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Service, Order, UserProfile

# --- 🏠 NAVIGATION & GENERAL ---

def home(request):
    """Landing page featuring featured services."""
    services = Service.objects.all()[:3]
    return render(request, 'core/index.html', {'services': services})

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

def services_page(request):
    """Main hub for print services and pricing engine."""
    services = Service.objects.all()
    return render(request, 'core/services.html', {
        'services': services, 
        'first_service': services.first()
    })

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def terms_conditions(request):
    return render(request, 'core/terms_conditions.html')


# --- 👤 AUTHENTICATION HUB ---

def register_view(request):
    """Handles student account creation using mobile as username."""
    if request.method == "POST":
        full_name = request.POST.get('username') # Map 'username' input to first_name
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        address = request.POST.get('address')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=mobile).exists():
            messages.error(request, "This mobile number is already registered.")
            return redirect('register')

        # Create User with mobile as username for login consistency
        user = User.objects.create_user(username=mobile, password=password, email=email, first_name=full_name)
        UserProfile.objects.create(user=user, mobile=mobile, address=address)
        
        messages.success(request, "Registration successful! Please login.")
        return redirect('login')
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        pw = request.POST.get('password')
        user = authenticate(request, username=mobile, password=pw)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('profile')
        messages.error(request, "Invalid mobile number or password.")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')


# --- 📊 PROFILE & STUDENT DASHBOARD ---

@login_required(login_url='login')
def profile_view(request):
    """Dashboard displaying user details and unique order logs."""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # DATABASE SAFETY WRAPPER: Prevents crash if table is missing or empty
    try:
        user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
        tracking = user_orders.exclude(status='Delivered').first()
        recent_bookings = user_orders[:5]
    except Exception:
        tracking = None
        recent_bookings = []

    return render(request, 'core/profile.html', {
        'profile': profile,
        'recent_bookings': recent_bookings,
        'tracking': tracking,
    })

@login_required(login_url='login')
def edit_profile(request):
    """Dedicated profile update page."""
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        new_name = request.POST.get('name')
        new_mobile = request.POST.get('mobile')
        new_address = request.POST.get('address')

        if User.objects.filter(username=new_mobile).exclude(id=request.user.id).exists():
            messages.error(request, "Mobile number already in use.")
            return redirect('edit_profile')

        try:
            request.user.first_name = new_name
            request.user.username = new_mobile # Update login credential
            request.user.save()
            profile.mobile = new_mobile
            profile.address = new_address
            profile.save()
            messages.success(request, "Profile details updated!")
            return redirect('profile')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
    return render(request, 'core/edit_profile.html', {'profile': profile})

@login_required(login_url='login')
def history_view(request):
    """Full order history with database safety check."""
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    except Exception:
        orders = []
    return render(request, 'core/history.html', {'orders': orders})


# --- 🛒 CART & ORDER PROCESSING ---

@login_required(login_url='login')
def cart_page(request):
    """Calculates live bill for items stored in the session."""
    cart_items = request.session.get('cart', [])
    total_bill = sum(float(item.get('total_price', 0)) for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total_bill': total_bill})

@login_required(login_url='login')
def add_to_cart(request):
    """Saves a print configuration to the temporary session cart."""
    if request.method == "POST":
        item = {
            'service_name': request.POST.get('service_name'),
            'total_price': request.POST.get('total_price_hidden'),
            'document_name': request.FILES['document'].name if 'document' in request.FILES else "Document.pdf"
        }
        cart = request.session.get('cart', [])
        cart.append(item)
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    """Removes specific item by index from user session."""
    cart_list = request.session.get('cart', [])
    if 0 <= item_id < len(cart_list):
        cart_list.pop(item_id)
        request.session['cart'] = cart_list
        request.session.modified = True
    return redirect('cart')

@login_required(login_url='login')
def order_all(request):
    """Converts every item in the cart into a permanent, unique Order record."""
    if request.method == "POST":
        cart_items = request.session.get('cart', [])
        if not cart_items:
            messages.warning(request, "Cart is empty!")
            return redirect('services')

        for item in cart_items:
            # Create a separate order instance for each document
            Order.objects.create(
                user=request.user,
                service_name=item.get('service_name'),
                total_price=float(item.get('total_price', 0)),
                status='Pending'
            )
        
        request.session['cart'] = [] # Reset cart on success
        messages.success(request, f"Placed {len(cart_items)} unique orders successfully!")
        return redirect('profile')
    return redirect('cart')


# --- 📄 PDF ANALYSIS (AJAX) ---

def calculate_pages(request):
    """Server-side PDF processing for page detection via AJAX."""
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            pdf_file = request.FILES['document']
            # Read PDF without saving to disk for speed
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
            pages = len(reader.pages)
            return JsonResponse({'success': True, 'pages': pages})
        except Exception:
            return JsonResponse({'success': False, 'message': "Could not read PDF file."})
    return JsonResponse({'success': False})