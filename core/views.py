import re  # Crucial: Fixed the NameError
import PyPDF2
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Service, Order, UserProfile

# --- 👤 AUTHENTICATION & REGISTRATION HUB ---

def register_view(request):
    """Handles student registration with strict Regex validation."""
    if request.method == "POST":
        full_name = request.POST.get('name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        address = request.POST.get('address', '').strip()

        # 1. Name Validation (Only letters and spaces)
        if not re.match(r"^[a-zA-Z\s]+$", full_name):
            messages.error(request, "Registration Failed: Name must contain only letters.")
            return redirect('register')

        # 2. Mobile Validation (Exactly 10 digits)
        if not re.match(r"^\d{10}$", mobile):
            messages.error(request, "Registration Failed: Mobile number must be exactly 10 digits.")
            return redirect('register')

        # 3. Password Length Validation (Min 6 characters)
        if len(password) < 6:
            messages.error(request, "Registration Failed: Password must be at least 6 characters long.")
            return redirect('register')

        if password != confirm_password:
            messages.error(request, "Registration Failed: Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Registration Failed: This mobile number is already registered.")
            return redirect('register')

        try:
            # Create User (Using mobile as username for login)
            user = User.objects.create_user(
                username=mobile, 
                password=password, 
                email=email, 
                first_name=full_name
            )
            UserProfile.objects.create(user=user, mobile=mobile, address=address)
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Database Error: {str(e)}")
            
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == "POST":
        mobile = request.POST.get('mobile')
        pw = request.POST.get('password')
        user = authenticate(request, username=mobile, password=pw)
        if user:
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}!")
            return redirect('profile')
        messages.error(request, "Invalid mobile number or password.")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# --- 📊 PROFILE & STUDENT DASHBOARD ---

@login_required(login_url='login')
def profile_view(request):
    """
    Renders the student dashboard. 
    Uses get_or_create to prevent 404 errors for Superusers/Admin.
    """
    # This replaces get_object_or_404
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'mobile': 'Not Provided', 'address': 'Not Provided'}
    )
    
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
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        
        # Validation for Edit Profile
        if not re.match(r"^[a-zA-Z\s]+$", name):
            messages.error(request, "Update Failed: Name should only contain letters.")
            return redirect('edit_profile')
        
        if not re.match(r"^\d{10}$", mobile):
            messages.error(request, "Update Failed: Invalid 10-digit mobile number.")
            return redirect('edit_profile')

        request.user.first_name = name
        request.user.username = mobile # Sync login ID
        request.user.save()
        
        profile.mobile = mobile
        profile.address = request.POST.get('address')
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    return render(request, 'core/edit_profile.html', {'profile': profile})

@login_required(login_url='login')
def history_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/history.html', {'orders': orders})

# --- 🛒 CART & ORDERING SYSTEM ---

@login_required(login_url='login')
def cart_page(request):
    cart_items = request.session.get('cart', [])
    total_bill = sum(float(item.get('total_price', 0)) for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total_bill': total_bill})

@login_required(login_url='login')
def add_to_cart(request):
    if request.method == "POST":
        item = {
            'service_name': request.POST.get('service_name'),
            'total_price': request.POST.get('total_price_hidden'),
            'document_name': request.FILES['document'].name if 'document' in request.FILES else "File.pdf"
        }
        cart = request.session.get('cart', [])
        cart.append(item)
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart_list = request.session.get('cart', [])
    if 0 <= item_id < len(cart_list):
        cart_list.pop(item_id)
        request.session['cart'] = cart_list
        request.session.modified = True
    return redirect('cart')

@login_required(login_url='login')
def order_all(request):
    if request.method == "POST":
        cart_items = request.session.get('cart', [])
        if not cart_items:
            messages.warning(request, "Your cart is empty.")
            return redirect('services')
            
        for item in cart_items:
            Order.objects.create(
                user=request.user,
                service_name=item.get('service_name'),
                total_price=float(item.get('total_price', 0)),
                status='Pending'
            )
        request.session['cart'] = []
        messages.success(request, f"Successfully placed {len(cart_items)} unique orders!")
        return redirect('profile')
    return redirect('cart')

# --- 📄 PDF ENGINE & UTILS ---

def calculate_pages(request):
    """AJAX endpoint for PDF page counting."""
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            pdf_data = request.FILES['document'].read()
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            return JsonResponse({'success': True, 'pages': len(reader.pages)})
        except:
            return JsonResponse({'success': False, 'message': 'Invalid PDF file.'})
    return JsonResponse({'success': False})

def home(request):
    services = Service.objects.all()[:3]
    return render(request, 'core/index.html', {'services': services})

def services_page(request):
    services = Service.objects.all()
    return render(request, 'core/services.html', {'services': services, 'first_service': services.first()})

def about(request): return render(request, 'core/about.html')
def contact(request): return render(request, 'core/contact.html')
def privacy_policy(request): return render(request, 'core/privacy_policy.html')
def terms_conditions(request): return render(request, 'core/terms_conditions.html')