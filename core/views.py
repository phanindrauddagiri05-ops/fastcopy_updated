import io
import uuid
import PyPDF2
import hashlib
import base64
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Service, Order, UserProfile

# --- 👤 1. AUTHENTICATION & PROFILE HUB ---

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == "POST":
        full_name = request.POST.get('name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '')
        
        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return redirect('register')
            
        user = User.objects.create_user(username=mobile, password=password, first_name=full_name)
        UserProfile.objects.create(user=user, mobile=mobile)
        messages.success(request, "Account created! Please login.")
        return redirect('login')
    return render(request, 'core/register.html')

def login_view(request):
    """
    Handles authentication and returns user to the service they 
    were trying to access via the 'next' parameter.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        mobile = request.POST.get('mobile')
        pw = request.POST.get('password')
        user = authenticate(request, username=mobile, password=pw)
        
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            
            # This handles the redirect back to the service/upload form
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'home')
        else:
            messages.error(request, "Invalid mobile number or password.")
            
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='login')
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    active_tracking = orders.exclude(status='Delivered').first()
    return render(request, 'core/profile.html', {
        'profile': profile,
        'recent_bookings': orders[:5],
        'tracking': active_tracking,
    })

@login_required(login_url='login')
def edit_profile(request):
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
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/history.html', {'orders': orders})

# --- 🛒 2. CART & PDF ENGINE ---

def calculate_pages(request):
    """AJAX endpoint for real-time PDF page counting."""
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(request.FILES['document'].read()))
            return JsonResponse({'success': True, 'pages': len(pdf_reader.pages)})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def add_to_cart(request):
    """
    AJAX view to handle file uploads. 
    Manual check ensures safety if JS is bypassed.
    """
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False, 
                'message': 'User must be login before uploading the document'
            }, status=401)

        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            return JsonResponse({'success': False, 'message': 'No file selected'})

        ext = uploaded_file.name.split('.')[-1].lower()
        file_path = None
        image_path = None

        # Logic for PDF vs Image
        if ext == 'pdf':
            file_path = default_storage.save(f'temp/{uuid.uuid4()}_{uploaded_file.name}', ContentFile(uploaded_file.read()))
        else:
            image_path = default_storage.save(f'temp_img/{uuid.uuid4()}_{uploaded_file.name}', ContentFile(uploaded_file.read()))
        
        item = {
            'service_name': request.POST.get('service_name'),
            'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name,
            'temp_path': file_path,
            'temp_image_path': image_path,
            'copies': request.POST.get('copies', 1),
            'location': request.POST.get('location'),
            'print_mode': request.POST.get('print_mode'),
            'side_type': request.POST.get('side_type', 'single'),
        }
        
        cart = request.session.get('cart', [])
        cart.append(item)
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'success': True})
    
@login_required(login_url='login')
def cart_page(request):
    cart_items = request.session.get('cart', [])
    total_bill = sum(float(i.get('total_price', 0)) for i in cart_items)
    return render(request, 'core/cart.html', {
        'cart_items': cart_items, 
        'total_bill': round(total_bill, 2)
    })

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

# --- 🚀 3. ORDER PLACEMENT & PAYMENT ---

@login_required(login_url='login')
def order_all(request):
    if request.method == "POST":
        cart_items = request.session.get('cart', [])
        
        # 1. Safety Check: If cart is empty, send them back
        if not cart_items:
            messages.warning(request, "Your cart is empty.")
            return redirect('cart')

        batch_id = str(uuid.uuid4())[:12].upper()
        last_order = None

        for item in cart_items:
            temp_path = item.get('temp_path')
            temp_img_path = item.get('temp_image_path')

            # We check if AT LEAST one of the file paths exists
            if (temp_path and default_storage.exists(temp_path)) or (temp_img_path and default_storage.exists(temp_img_path)):
                
                # Logic to handle PDF data if it exists
                pdf_file = None
                if temp_path and default_storage.exists(temp_path):
                    with default_storage.open(temp_path) as f:
                        pdf_file = ContentFile(f.read(), name=item.get('document_name'))

                # Logic to handle Image data if it exists
                img_file = None
                if temp_img_path and default_storage.exists(temp_img_path):
                    with default_storage.open(temp_img_path) as f:
                        img_file = ContentFile(f.read(), name=temp_img_path.split('_')[-1])

                # 2. Create the Order
                order = Order.objects.create(
                    user=request.user,
                    service_name=item.get('service_name'),
                    total_price=float(item.get('total_price', 0)),
                    document=pdf_file,
                    image_upload=img_file,
                    location=item.get('location'),
                    print_mode=item.get('print_mode'),
                    custom_color_pages=item.get('custom_color_pages', ''),
                    side_type=item.get('side_type'),
                    copies=item.get('copies'),
                    transaction_id=batch_id
                )
                last_order = order
                
                # Cleanup temp files
                if temp_path: default_storage.delete(temp_path)
                if temp_img_path: default_storage.delete(temp_img_path)

        # 3. Final Safety Check: Did we actually create any orders?
        if last_order:
            request.session['cart'] = [] # Clear cart only on success
            request.session.modified = True
            return redirect('checkout_summary', order_id=last_order.id)
        else:
            messages.error(request, "Could not process order. Files may have expired. Please re-upload.")
            return redirect('cart')

    return redirect('cart')

@login_required(login_url='login')
def order_now(request):
    """Direct purchase logic bypassing the cart, sending user to payment."""
    if request.method == "POST":
        uploaded_file = request.FILES.get('document')
        if uploaded_file:
            order = Order.objects.create(
                user=request.user,
                service_name=request.POST.get('service_name'),
                total_price=float(request.POST.get('total_price_hidden', 0)),
                document=uploaded_file,
                location=request.POST.get('location'),
                print_mode=request.POST.get('print_mode'),
                custom_color_pages=request.POST.get('custom_color_pages'),
                side_type=request.POST.get('side_type'),
                copies=request.POST.get('copies', 1),
                status='Pending',
                payment_status='Pending'
            )
            return redirect('checkout_summary', order_id=order.id)
    return redirect('services')

# --- 💳 4. PHONEPE INTEGRATION ---

def get_phonepe_token():
    """Exchanges keys for OAuth2 token with terminal debugging."""
    data = {
        'client_id': settings.PHONEPE_CLIENT_ID,
        'client_secret': settings.PHONEPE_CLIENT_SECRET,
        'grant_type': 'client_credentials',
    }
    try:
        response = requests.post(settings.PHONEPE_AUTH_URL, data=data)
        print(f"PHONEPE AUTH STATUS: {response.status_code}")
        print(f"PHONEPE AUTH RESPONSE: {response.text}")

        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
    return None

def checkout_summary(request, order_id):
    """Displays order confirmation before initiating payment."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/checkout.html', {'order': order})

def initiate_payment(request, order_id):
    """Starts the PhonePe Pay Page flow."""
    order = get_object_or_404(Order, id=order_id)
    token = get_phonepe_token()
    
    if not token:
        # UPDATED PATH TO core/
        return render(request, 'core/payment_failed.html', {
            "order": order, 
            "error": "Authentication with Payment Gateway Failed."
        })

    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    base_url = f"{scheme}://{host}"

    txn_id = f"TXN_{uuid.uuid4().hex[:10].upper()}"
    order.transaction_id = txn_id
    order.save()

    payload = {
        "merchantId": settings.PHONEPE_MERCHANT_ID,
        "merchantTransactionId": txn_id,
        "merchantUserId": f"USER_{request.user.id}",
        "amount": int(order.total_price * 100),
        "redirectUrl": f"{base_url}/payment/callback/",
        "redirectMode": "POST",
        "callbackUrl": f"{base_url}/payment/callback/",
        "paymentInstrument": {"type": "PAY_PAGE"}
    }

    base64_payload = base64.b64encode(json.dumps(payload).encode()).decode()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            settings.PHONEPE_PAY_URL,
            json={"request": base64_payload},
            headers=headers
        )
        res_data = response.json()

        if res_data.get('success'):
            pay_url = res_data['data']['instrumentResponse']['redirectInfo']['url']
            return redirect(pay_url)
        else:
            # UPDATED PATH TO core/
            return render(request, 'core/payment_failed.html', {
                "order": order, 
                "error": res_data.get('message', 'Gateway rejection')
            })
            
    except Exception as e:
        # UPDATED PATH TO core/
        return render(request, 'core/payment_failed.html', {'order_id': order_id})
    
@csrf_exempt
def payment_callback(request):
    """Handles logic after the user returns from PhonePe."""
    if request.method == "POST":
        merchant_txn_id = request.POST.get('merchantTransactionId')
        code = request.POST.get('code')
        
        order = get_object_or_404(Order, transaction_id=merchant_txn_id)
        
        if code == 'PAYMENT_SUCCESS':
            order.payment_status = "Success"
            order.status = "Ready"
            order.save()
            # UPDATED PATH TO core/
            return render(request, 'core/payment_success.html', {'order': order})
        else:
            order.payment_status = "Failed"
            order.save()
            # UPDATED PATH TO core/
            return render(request, 'core/payment_failed.html', {'order_id': order_id})
            
    return redirect('home')

# --- 🌐 5. STATIC PAGES ---

def home(request):
    services = Service.objects.all()[:3]
    return render(request, 'core/index.html', {'services': services})

def services_page(request):
    return render(request, 'core/services.html', {'services': Service.objects.all()})

def about(request): return render(request, 'core/about.html')
def contact(request): return render(request, 'core/contact.html')
def privacy_policy(request): return render(request, 'core/privacy_policy.html')
def terms_conditions(request): return render(request, 'core/terms_conditions.html')