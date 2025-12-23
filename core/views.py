import re
import PyPDF2
import io
import uuid
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Service, Order, UserProfile

# --- 👤 1. AUTHENTICATION & REGISTRATION ---

def register_view(request):
    """Handles new student registration and creates UserProfile."""
    if request.method == "POST":
        full_name = request.POST.get('name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '')
        
        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return redirect('register')
            
        try:
            user = User.objects.create_user(username=mobile, password=password, first_name=full_name)
            UserProfile.objects.create(user=user, mobile=mobile, address='')
            messages.success(request, "Account created! Please login.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
    return render(request, 'core/register.html')

def login_view(request):
    """Authenticates user via mobile number."""
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get('mobile'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('profile')
        messages.error(request, "Invalid credentials.")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# --- 📊 2. PROFILE & DASHBOARD ---

@login_required(login_url='login')
def profile_view(request):
    """Dashboard showing recent orders and status tracking."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    active_tracking = orders.exclude(status='Delivered').first()
    return render(request, 'core/profile.html', {
        'profile': profile, 
        'recent_bookings': orders[:5], 
        'tracking': active_tracking
    })

@login_required(login_url='login')
def edit_profile(request):
    """Allows updating name and address."""
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        request.user.first_name = request.POST.get('name')
        request.user.save()
        profile.address = request.POST.get('address')
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    return render(request, 'core/edit_profile.html', {'profile': profile})

@login_required(login_url='login')
def history_view(request):
    """Full order history."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/history.html', {'orders': orders})

# --- 🛒 3. CART & ORDERING SYSTEM (FILE STORAGE) ---

@login_required(login_url='login')
def add_to_cart(request):
    """AJAX: Saves file to media/temp and metadata to session."""
    if request.method == "POST":
        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            return JsonResponse({'success': False, 'message': 'No file uploaded'})

        # Secure file storage in temporary folder
        file_path = default_storage.save(f'temp/{uuid.uuid4()}_{uploaded_file.name}', ContentFile(uploaded_file.read()))
        
        item = {
            'service_name': request.POST.get('service_name'),
            'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name,
            'temp_path': file_path,
            'copies': request.POST.get('copies', 1),
            'print_type': request.POST.get('print_type', 'Standard')
        }
        
        cart = request.session.get('cart', [])
        cart.append(item)
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='login')
def cart_page(request):
    cart_items = request.session.get('cart', [])
    total_bill = sum(float(item.get('total_price', 0)) for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total_bill': round(total_bill, 2)})

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart = request.session.get('cart', [])
    if 0 <= item_id < len(cart):
        item = cart.pop(item_id)
        if default_storage.exists(item.get('temp_path', '')):
            default_storage.delete(item['temp_path'])
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')

@login_required(login_url='login')
def order_all(request):
    """Processes checkout for all items in the cart."""
    if request.method == "POST":
        cart_items = request.session.get('cart', [])
        for item in cart_items:
            temp_path = item.get('temp_path')
            if temp_path and default_storage.exists(temp_path):
                with default_storage.open(temp_path) as f:
                    Order.objects.create(
                        order_id=str(uuid.uuid4())[:8].upper(),
                        user=request.user,
                        service_name=item.get('service_name'),
                        total_price=float(item.get('total_price', 0)),
                        document=ContentFile(f.read(), name=item.get('document_name')),
                        status='Pending'
                    )
                default_storage.delete(temp_path)
        request.session['cart'] = []
        messages.success(request, "All orders placed successfully!")
        return redirect('profile')
    return redirect('cart')

@login_required(login_url='login')
def order_now(request):
    """Handles immediate direct ordering."""
    if request.method == "POST":
        uploaded_file = request.FILES.get('document')
        if uploaded_file:
            Order.objects.create(
                order_id=str(uuid.uuid4())[:8].upper(),
                user=request.user,
                service_name=request.POST.get('service_name'),
                total_price=float(request.POST.get('total_price_hidden', 0)),
                document=uploaded_file,
                status='Pending'
            )
            messages.success(request, "Order placed successfully!")
            return redirect('profile')
    return redirect('services')

# --- 📄 4. PDF ENGINE & UTILS ---

def calculate_pages(request):
    """Real-time PDF page counting."""
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(request.FILES['document'].read()))
            return JsonResponse({'success': True, 'pages': len(pdf_reader.pages)})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

# --- 🌐 5. STATIC PAGES ---

def home(request):
    return render(request, 'core/index.html', {'services': Service.objects.all()[:3]})

def services_page(request):
    return render(request, 'core/services.html', {'services': Service.objects.all()})

def about(request): return render(request, 'core/about.html')
def contact(request): return render(request, 'core/contact.html')
def privacy_policy(request): return render(request, 'core/privacy_policy.html')
def terms_conditions(request): return render(request, 'core/terms_conditions.html')