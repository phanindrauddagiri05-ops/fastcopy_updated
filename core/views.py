import io, uuid, PyPDF2, base64, json, requests, hashlib, time
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
from django.db import transaction

from .models import Service, Order, UserProfile, CartItem, PricingConfig, Location
from .utils import calculate_delivery_date



# --- 🚀 0. CORE LOGIC ENGINES (Success/Failure/Helper) ---

<<<<<<< HEAD
def get_user_pricing(user):
    """
    Get appropriate pricing configuration based on user type.
    Returns dict with all prices for the specific user (dealer vs regular).
    """
    config = PricingConfig.get_config()
    
    # Check if user is a dealer
    try:
        profile = user.userprofile
        is_dealer = profile.is_dealer
    except:
        is_dealer = False
    
    base_dict = {
        'price_per_page': float(config.dealer_price_per_page) if is_dealer else float(config.admin_price_per_page),
        'soft_binding': float(config.soft_binding_price_dealer) if is_dealer else float(config.soft_binding_price_admin),
        'color_addition': float(config.color_price_addition_dealer) if is_dealer else float(config.color_price_addition_admin),
        'is_dealer': is_dealer,
        
        # Spiral Tiers
        'spiral_tier1_limit': config.spiral_tier1_limit,
        'spiral_tier2_limit': config.spiral_tier2_limit,
        'spiral_tier3_limit': config.spiral_tier3_limit,
        
        'spiral_tier1_price': float(config.spiral_tier1_price_dealer) if is_dealer else float(config.spiral_tier1_price_admin),
        'spiral_tier2_price': float(config.spiral_tier2_price_dealer) if is_dealer else float(config.spiral_tier2_price_admin),
        'spiral_tier3_price': float(config.spiral_tier3_price_dealer) if is_dealer else float(config.spiral_tier3_price_admin),
        'spiral_extra_price': float(config.spiral_extra_price_dealer) if is_dealer else float(config.spiral_extra_price_admin),
        
        # Custom Layouts
        'custom_1_4_price': float(config.custom_1_4_price_dealer) if is_dealer else float(config.custom_1_4_price_admin),
        'custom_1_8_price': float(config.custom_1_8_price_dealer) if is_dealer else float(config.custom_1_8_price_admin),
        'custom_1_9_price': float(config.custom_1_9_price_dealer) if is_dealer else float(config.custom_1_9_price_admin),
        'delivery_charge': float(config.delivery_price_dealer) if is_dealer else float(config.delivery_price_admin),
    }
    
    # Legacy support if needed, but we don't use 'custom_print_base' anymore
    return base_dict

def handle_failed_order(user, items_list, txn_id, reason="Payment Failed"):
    """
    DATABASE UPDATE LOGIC:
    Targets specific records by txn_id.
    Uses zip to match items to orders since duplicate files are allowed.
=======
def handle_failed_order(user, items_list, txn_id, reason="Payment Failed"):
    """
    DATABASE UPDATE LOGIC:
    Targets specific records by txn_id and document name to update statuses.
    Ensures 'Failed' and 'Cancelled' reflect in the database and user history.
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
    """
    if not txn_id:
        return None

    with transaction.atomic():
        # Get orders ordered by ID to match creation sequence
        db_orders = list(Order.objects.filter(transaction_id=txn_id).order_by('id'))
        last_order = None
<<<<<<< HEAD
        
        for item, order in zip(items_list, db_orders):
            if not item or not order: continue
            
            # Update order
            order.user = user
            order.service_name = item.get('service_name')
            order.total_price = float(item.get('total_price', 0))
            order.location = item.get('location')
            order.print_mode = item.get('print_mode')
            order.side_type = item.get('side_type')
            order.copies = item.get('copies')
            order.pages = item.get('pages', 1)
            order.custom_color_pages = item.get('custom_color_pages')
            order.payment_status = "Failed"
            order.status = "Cancelled"
            order.save()
            last_order = order
            
            # [STRICT] Restore to DB Cart if it was a Direct Order
=======
        for item in items_list:
            if not item: 
                continue
                
            # Update the existing Pending record or create a new Cancelled one if not found
            last_order, created = Order.objects.update_or_create(
                transaction_id=txn_id,
                document=item.get('document_name'),
                defaults={
                    'user': user,
                    'service_name': item.get('service_name'),
                    'total_price': float(item.get('total_price', 0)),
                    'location': item.get('location'),
                    'print_mode': item.get('print_mode'),
                    'side_type': item.get('side_type'),
                    'copies': item.get('copies'),
                    'pages': item.get('pages', 1),
                    'custom_color_pages': item.get('custom_color_pages'),
                    'payment_status': "Failed", # <-- Permanent DB Status
                    'status': "Cancelled"       # <-- Permanent DB Status
                }
            )
            
            # [STRICT] Restore to DB Cart if it was a Direct Order so user doesn't lose progress
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
            if txn_id.startswith("DIR"):
                CartItem.objects.get_or_create(
                    user=user,
                    document_name=item.get('document_name'),
                    defaults={
                        'service_name': item.get('service_name'),
                        'total_price': item.get('total_price'),
                        'temp_path': item.get('temp_path'),
                        'temp_image_path': item.get('temp_image_path'),
                        'copies': item.get('copies'),
                        'pages': item.get('pages', 1),
                        'location': item.get('location'),
                        'print_mode': item.get('print_mode'),
                        'side_type': item.get('side_type'),
                        'custom_color_pages': item.get('custom_color_pages')
                    }
                )
        return last_order

def process_successful_order(user, items_list, txn_id):
    """
    DATABASE UPDATE LOGIC:
<<<<<<< HEAD
    Updates records to 'Success' and 'Pending'.
    Uses zip to match items to orders.
    """
    with transaction.atomic():
        db_orders = list(Order.objects.filter(transaction_id=txn_id).order_by('id'))
        
        for item, order in zip(items_list, db_orders):
            if not item or not order: continue
=======
    Updates records to 'Success' and 'Pending' (for admin processing).
    """
    with transaction.atomic():
        for item in items_list:
            if not item: continue
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
                
            saved_pdf, saved_img = None, None
            path = item.get('temp_path') or item.get('temp_image_path')
            
            if path and default_storage.exists(path):
                with default_storage.open(path) as f:
                    content = ContentFile(f.read(), name=item['document_name'])
                    if item.get('temp_path'): saved_pdf = content
                    else: saved_img = content
            
<<<<<<< HEAD
            # Update order
            order.user = user
            order.service_name = item['service_name']
            order.total_price = float(item['total_price'])
            order.location = item['location']
            order.print_mode = item['print_mode']
            order.side_type = item['side_type']
            order.copies = item['copies']
            order.custom_color_pages = item.get('custom_color_pages', '')
            order.payment_status = "Success"
            order.status = "Pending"
            
            if saved_pdf: order.document = saved_pdf
            if saved_img: order.image_upload = saved_img
            
            order.save()
=======
            Order.objects.update_or_create(
                transaction_id=txn_id,
                document=item.get('document_name'),
                defaults={
                    'user': user,
                    'service_name': item['service_name'],
                    'total_price': float(item['total_price']),
                    'location': item['location'],
                    'print_mode': item['print_mode'],
                    'side_type': item['side_type'],
                    'copies': item['copies'],
                    'custom_color_pages': item.get('custom_color_pages', ''),
                    'payment_status': "Success",
                    'status': "Pending",
                    'document': saved_pdf,
                    'image_upload': saved_img,
                }
            )
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
            
            if item.get('temp_path') and default_storage.exists(item['temp_path']):
                default_storage.delete(item['temp_path'])
            if item.get('temp_image_path') and default_storage.exists(item['temp_image_path']):
                default_storage.delete(item['temp_image_path'])
<<<<<<< HEAD

# ... (Auth views skipped) ...

# ... (Around line 330 initiate_payment) ...

@login_required(login_url='login')
def initiate_payment(request):
    batch_txn_id = request.session.get('pending_batch_id')
    direct_item = request.session.get('direct_item')
    cart_items = request.session.get('cart', [])

    if not batch_txn_id: return redirect('cart')

    if batch_txn_id.startswith("DIR"):
        items_to_process = [direct_item] if direct_item else []
    else:
        items_to_process = cart_items

    if not items_to_process: return redirect('cart')

    unique_order_id = f"{batch_txn_id}_{int(time.time())}"
    with transaction.atomic():
        for item in items_to_process:
            # ALWAYS CREATE NEW RECORDS - DO NOT UPDATE_OR_CREATE
            # This ensures duplicate items get distinct records
            Order.objects.create(
                transaction_id=unique_order_id, 
                document=item.get('document_name'), # Note: document field logic handles file path, this just sets filename temporarily or is ignored if file field set? 
                # Actually document field is FileField. setting string might be weird?
                # In original code: document=item.get('document_name') works because it's CharField in database? No it's FileField.
                # But wait, original code: document=item.get('document_name').
                # If FileField, assigning string might fail? 
                # Actually earlier models.py showed: document = models.FileField(...)
                # BUT also: document_name = models.CharField(...)
                # Let's check initiate_payment original code...
                # It passed `document=item.get('document_name')`.
                # If that works, it means Django handles it? Or `document_name` is separate?
                # Ah, checking models.py: line 160 `document_name = models.CharField`.
                # line 102 `document = models.FileField`.
                # The original code at line 348 passed `document=item.get('document_name')`.
                # This seems WRONG if target is `document` (FileField).
                # `document_name` field exists!
                # Maybe I should pass keys explicitly.
                
                # Correcting to use explicit field mapping for safety
                user=request.user,
                service_name=item.get('service_name'),
                total_price=float(item.get('total_price', 0)),
                location=item.get('location'),
                print_mode=item.get('print_mode'),
                side_type=item.get('side_type'),
                copies=item.get('copies'),
                pages=item.get('pages', 1),
                custom_color_pages=item.get('custom_color_pages', ''),
                payment_status="Pending",
                status="Pending",
                document_name=item.get('document_name') # Explicitly save name
            )
=======
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc

# --- 👤 1. AUTHENTICATION & PROFILE ---

def register_view(request):
    if request.user.is_authenticated: return redirect('home')
    if request.method == "POST":
        full_name = request.POST.get('name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        address = request.POST.get('address', '').strip()

        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return redirect('register')

        user = User.objects.create_user(username=mobile, password=password, first_name=full_name, email=email)
        UserProfile.objects.create(user=user, mobile=mobile, address=address)
        messages.success(request, "Account created successfully! Please login.")
        return redirect('login')
    return render(request, 'core/register.html')

def login_view(request):
    if request.user.is_authenticated: return redirect('home')
    if request.method == "POST":
        mobile, pw = request.POST.get('mobile'), request.POST.get('password')
        user = authenticate(request, username=mobile, password=pw)
        if user:
            login(request, user)
<<<<<<< HEAD
            return redirect('home') 
=======
            return redirect('cart') 
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
        messages.error(request, "Invalid login credentials.")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request); return redirect('home')

@login_required(login_url='login')
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {'profile': profile, 'user_name': request.user.first_name, 'user_email': request.user.email, 'recent_bookings': orders[:5]}
    return render(request, 'core/profile.html', context)

@login_required(login_url='login')
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        request.user.first_name = request.POST.get('name')
        request.user.email = request.POST.get('email')
        request.user.username = request.POST.get('mobile') 
        request.user.save()
        profile.mobile = request.POST.get('mobile')
        profile.address = request.POST.get('address')
        profile.save()
        messages.success(request, "Updated successfully!")
        return redirect('profile')
    return render(request, 'core/edit_profile.html', {'profile': profile})

@login_required(login_url='login')
def history_view(request):
    all_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/history.html', {'orders': all_orders})

# --- 🛒 2. CART & PDF ENGINE ---

def calculate_pages(request):
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(request.FILES['document'].read()))
            return JsonResponse({'success': True, 'pages': len(pdf_reader.pages)})
        except: return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def add_to_cart(request):
    if request.method == "POST" and request.user.is_authenticated:
        uploaded_file = request.FILES.get('document')
        if not uploaded_file: return JsonResponse({'success': False})
        file_path = default_storage.save(f'temp/{uuid.uuid4()}_{uploaded_file.name}', ContentFile(uploaded_file.read()))
        service_name = request.POST.get('service_name')
        print_mode = request.POST.get('print_mode', 'B&W')
        item = {
            'service_name': service_name, 'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name, 'temp_path': file_path if uploaded_file.name.endswith('.pdf') else None,
            'temp_image_path': file_path if not uploaded_file.name.endswith('.pdf') else None, 
            'copies': int(request.POST.get('copies', 1)), 'pages': int(request.POST.get('page_count', 1)), 
            'location': request.POST.get('location'), 'print_mode': print_mode, 
            'side_type': request.POST.get('side_type', 'single'), 'custom_color_pages': request.POST.get('custom_color_pages', ''),
        }
        CartItem.objects.create(user=request.user, **item)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=401)

@login_required(login_url='login')
def cart_page(request):
    db_items = CartItem.objects.filter(user=request.user).order_by('-created_at')
    cart_list = []
    for i in db_items:
        cart_list.append({
            'id': i.id,
            'service_name': i.service_name, 'total_price': str(i.total_price), 'document_name': i.document_name,
            'temp_path': i.temp_path, 'temp_image_path': i.temp_image_path, 'copies': i.copies, 'pages': i.pages,
            'location': i.location, 'print_mode': i.print_mode, 'side_type': i.side_type, 'custom_color_pages': i.custom_color_pages,
        })
    request.session['cart'] = cart_list
    request.session.modified = True
    total_bill = sum(float(i.total_price) for i in db_items)
    total_eff_pages = sum(int(i.pages) * int(i.copies) for i in db_items)
    context = {'cart_items': cart_list, 'total_bill': round(total_bill, 2), 'total_pages': total_eff_pages, 'min_required': 5}
    return render(request, 'core/cart.html', context)

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    name = item.service_name
    item.delete()
    messages.success(request, f"Removed '{name}' from your cart.")
    return redirect('cart')

# --- 🚀 3. ORDER & CHECKOUT FLOW ---

@login_required(login_url='login')
def order_all(request):
    cart = CartItem.objects.filter(user=request.user)
    if not cart.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
    if 'direct_item' in request.session: del request.session['direct_item']
    request.session['pending_batch_id'] = f"TXN_{uuid.uuid4().hex[:10].upper()}"
    request.session.modified = True
    return redirect('cart_checkout_summary')

@login_required(login_url='login')
def order_now(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get('document')
        if not uploaded_file: return redirect('services')
        file_path = default_storage.save(f'temp/direct_{uuid.uuid4()}_{uploaded_file.name}', ContentFile(uploaded_file.read()))
        request.session['direct_item'] = {
            'service_name': request.POST.get('service_name'), 'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name, 'temp_path': file_path if uploaded_file.name.endswith('.pdf') else None,
            'temp_image_path': file_path if not uploaded_file.name.endswith('.pdf') else None, 
            'copies': int(request.POST.get('copies', 1)), 'pages': int(request.POST.get('page_count', 1)), 
            'location': request.POST.get('location'), 'print_mode': request.POST.get('print_mode', 'B&W'), 
            'side_type': request.POST.get('side_type', 'single'), 'custom_color_pages': request.POST.get('custom_color_pages', ''),
        }
        request.session['pending_batch_id'] = f"DIR_{uuid.uuid4().hex[:10].upper()}"
        request.session.modified = True
        return redirect('cart_checkout_summary')
    return redirect('services')

@login_required(login_url='login')
def process_direct_order(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get('document')
        if not uploaded_file: return JsonResponse({'success': False})
        file_path = default_storage.save(f'temp/direct_{uuid.uuid4()}', ContentFile(uploaded_file.read()))
        direct_item = {
            'service_name': request.POST.get('service_name'), 'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name, 'temp_path': file_path if uploaded_file.name.endswith('.pdf') else None,
            'temp_image_path': file_path if not uploaded_file.name.endswith('.pdf') else None, 
            'copies': int(request.POST.get('copies', 1)), 'pages': int(request.POST.get('page_count', 1)), 
            'location': request.POST.get('location'), 'print_mode': request.POST.get('print_mode', 'B&W'), 
            'side_type': request.POST.get('side_type', 'single'), 'custom_color_pages': request.POST.get('custom_color_pages', ''),
        }
        request.session['direct_item'] = direct_item
        request.session['pending_batch_id'] = f"DIR_{uuid.uuid4().hex[:10].upper()}"
        request.session.modified = True
        return JsonResponse({'success': True, 'redirect_url': '/checkout/summary/'})
    return JsonResponse({'success': False})

@login_required(login_url='login')
def cart_checkout_summary(request):
    batch_txn_id = request.session.get('pending_batch_id', '')
    if batch_txn_id.startswith("DIR"):
        items = [request.session.get('direct_item')] if request.session.get('direct_item') else []
    else:
        items = request.session.get('cart', [])
    if not items or None in items: return redirect('services')
    grand_total = sum(float(i.get('total_price', 0)) for i in items)
<<<<<<< HEAD
    pricing = get_user_pricing(request.user)
    delivery_charge = pricing.get('delivery_charge', 0.0)
    grand_total += delivery_charge
    est_date = calculate_delivery_date()
    return render(request, 'core/checkout.html', {
        'cart_items': items, 
        'grand_total': round(grand_total, 2), 
        'items_count': len(items), 
        'delivery_charge': delivery_charge,
        'est_delivery_date': est_date
    })
=======
    return render(request, 'core/checkout.html', {'cart_items': items, 'grand_total': round(grand_total, 2), 'items_count': len(items)})
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc

# --- 💳 4. CASHFREE GATEWAY INTEGRATION ---

@login_required(login_url='login')
def initiate_payment(request):
    batch_txn_id = request.session.get('pending_batch_id')
    direct_item = request.session.get('direct_item')
    cart_items = request.session.get('cart', [])

    if not batch_txn_id: return redirect('cart')

    if batch_txn_id.startswith("DIR"):
        items_to_process = [direct_item] if direct_item else []
    else:
        items_to_process = cart_items

    if not items_to_process: return redirect('cart')

    unique_order_id = f"{batch_txn_id}_{int(time.time())}"
<<<<<<< HEAD
    est_date = calculate_delivery_date()
    
    with transaction.atomic():
        for item in items_to_process:
            # Create NEW record for every item to safely handle duplicates
            Order.objects.create(
                transaction_id=unique_order_id, 
                user=request.user,
                service_name=item.get('service_name'),
                total_price=float(item.get('total_price', 0)), 
                location=item.get('location'), 
                print_mode=item.get('print_mode'), 
                side_type=item.get('side_type'),
                copies=item.get('copies'), 
                pages=item.get('pages', 1), 
                custom_color_pages=item.get('custom_color_pages', ''), 
                estimated_delivery_date=est_date,
                payment_status="Pending", 
                status="Pending"
            )

    grand_total = sum(float(i.get('total_price', 0)) for i in items_to_process)
    pricing = get_user_pricing(request.user)
    grand_total += pricing.get('delivery_charge', 0.0)
    
=======
    with transaction.atomic():
        for item in items_to_process:
            Order.objects.update_or_create(
                transaction_id=unique_order_id, document=item.get('document_name'),
                defaults={'user': request.user, 'service_name': item.get('service_name'), 'total_price': float(item.get('total_price', 0)), 
                          'location': item.get('location'), 'print_mode': item.get('print_mode'), 'side_type': item.get('side_type'),
                          'copies': item.get('copies'), 'pages': item.get('pages', 1), 'custom_color_pages': item.get('custom_color_pages', ''), 
                          'payment_status': "Pending", 'status': "Pending"}
            )

    grand_total = sum(float(i.get('total_price', 0)) for i in items_to_process)
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
    callback_url = f"{request.scheme}://{request.get_host()}/payment/callback/"
    user_mobile = request.user.profile.mobile if hasattr(request.user, 'profile') else "9999999999"
    if not user_mobile.startswith('91'): user_mobile = f"91{user_mobile}"

    payload = {
        "order_id": unique_order_id, "order_amount": float(grand_total), "order_currency": "INR",
        "customer_details": {"customer_id": f"CUST_{request.user.id}", "customer_name": request.user.username, "customer_email": request.user.email or "test@fastcopy.in", "customer_phone": user_mobile},
        "order_meta": {"return_url": callback_url, "notify_url": callback_url}
    }
    headers = {"Content-Type": "application/json", "x-api-version": settings.CASHFREE_API_VERSION, "x-client-id": settings.CASHFREE_APP_ID, "x-client-secret": settings.CASHFREE_SECRET_KEY}
    
    try:
        response = requests.post(f"{settings.CASHFREE_API_URL}/orders", json=payload, headers=headers)
        res_json = response.json()
        if response.status_code == 200 and res_json.get('payment_session_id'):
            request.session['cashfree_payment_session_id'] = res_json.get('payment_session_id')
            request.session['cashfree_order_id'] = unique_order_id
            request.session.modified = True
            return redirect('cashfree_checkout')
        return redirect('cart')
    except: return redirect('cart')

<<<<<<< HEAD

# Ensure you import your helper functions
# from .views import process_successful_order, handle_failed_order 

@csrf_exempt
def payment_callback(request):
    """STRICT CALLBACK: Updates DB to Success or Failed/Cancelled."""
    
    # 1. Safely retrieve the Order ID from GET params or Session
=======
@csrf_exempt
def payment_callback(request):
    """STRICT CALLBACK: Updates DB to Success or Failed/Cancelled."""
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
    order_id = (request.GET.get('order_id') or 
                request.GET.get('orderId') or 
                request.session.get('cashfree_order_id'))

    if not order_id:
        messages.error(request, "Payment session not found. Returning to cart.")
<<<<<<< HEAD
        return redirect('cart')
    
    txn_id = order_id
    is_direct = str(txn_id).startswith("DIR")
    direct_item = request.session.get('direct_item')
    
    # Safely get items involved
    session_cart = request.session.get('cart', [])
    items_involved = [direct_item] if is_direct else session_cart

    # 2. Cashfree API Authentication Headers
    headers = {
        "Content-Type": "application/json",
        "x-api-version": settings.CASHFREE_API_VERSION,
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY
    }
    
    # 3. Verify Status with Payment Gateway
    order_status = 'FAILED' # Default fallback
    try:
        response = requests.get(
            f"{settings.CASHFREE_API_URL}/orders/{order_id}", 
            headers=headers,
            timeout=10 # Added timeout for safety
        )
        
        # Check if the response is actually JSON and successful
        if response.status_code == 200:
            json_data = response.json()
            if json_data: # Verify json_data is not None
                order_status = json_data.get('order_status', 'FAILED')
        else:
            print(f"Cashfree API Error: {response.status_code} - {response.text}")
            
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Network or JSON Parsing Error: {e}")
        order_status = 'FAILED'

    # 4. Process based on verified status
    if order_status == 'PAID':
        # Create records in Order table
        process_successful_order(request.user, items_involved, txn_id)
        
        # Clean up database and session
        if is_direct and direct_item: 
            CartItem.objects.filter(
                user=request.user, 
                document_name=direct_item.get('document_name')
            ).delete()
            if 'direct_item' in request.session: 
                del request.session['direct_item']
        else: 
            CartItem.objects.filter(user=request.user).delete()
            request.session['cart'] = []
            
        # Clear the temporary order ID
        if 'cashfree_order_id' in request.session:
            del request.session['cashfree_order_id']
            
        messages.success(request, "Payment successful! Your order has been placed.")
        return redirect('history')

    else:
        # LOG FAILED PAYMENT TO DATABASE
        handle_failed_order(request.user, items_involved, txn_id)
        
        # Restore session context for retry if it was a direct order
        if is_direct and direct_item:
            db_cart = CartItem.objects.filter(user=request.user)
            request.session['cart'] = [
                {
                    'id': i.id, 
                    'service_name': i.service_name, 
                    'total_price': str(i.total_price), 
                    'document_name': i.document_name
                } for i in db_cart
            ]
            if 'direct_item' in request.session: 
                del request.session['direct_item']

        messages.warning(request, "Payment was canceled or failed. Your items are safe in the cart.")
        return redirect('cart')
=======
        return redirect('cart')
    
    txn_id = order_id
    is_direct = txn_id.startswith("DIR")
    direct_item = request.session.get('direct_item')
    items_involved = [direct_item] if is_direct else request.session.get('cart', [])

    headers = {"Content-Type": "application/json", "x-api-version": settings.CASHFREE_API_VERSION, "x-client-id": settings.CASHFREE_APP_ID, "x-client-secret": settings.CASHFREE_SECRET_KEY}
    
    try:
        response = requests.get(f"{settings.CASHFREE_API_URL}/orders/{order_id}", headers=headers)
        order_status = response.json().get('order_status', 'FAILED')
    except: order_status = 'FAILED'

    if order_status == 'PAID':
        process_successful_order(request.user, items_involved, txn_id)
        if is_direct: 
            CartItem.objects.filter(user=request.user, document_name=direct_item.get('document_name')).delete()
            if 'direct_item' in request.session: del request.session['direct_item']
        else: 
            CartItem.objects.filter(user=request.user).delete()
            request.session['cart'] = []
        messages.success(request, "Payment successful! Order placed.")
        return redirect('history')
    else:
        # LOG FAILED PAYMENT TO DATABASE
        handle_failed_order(request.user, items_involved, txn_id)
        
        # Restore session context for retry
        if is_direct and direct_item:
            db_cart = CartItem.objects.filter(user=request.user)
            request.session['cart'] = [{'id': i.id, 'service_name': i.service_name, 'total_price': str(i.total_price), 'document_name': i.document_name} for i in db_cart]
            if 'direct_item' in request.session: del request.session['direct_item']

        messages.warning(request, "Payment was canceled or failed. Items are safe in your cart.")
        return redirect('cart')

>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
@login_required(login_url='login')
def cashfree_checkout(request):
    context = {'payment_session_id': request.session.get('cashfree_payment_session_id'), 'cashfree_env': 'sandbox'}
    return render(request, 'core/cashfree_checkout.html', context)

# --- 🌐 5. STATIC PAGES ---
def home(request): return render(request, 'core/index.html', {'services': Service.objects.all()[:3]})
def services_page(request):
    """Services page with dynamic pricing from PricingConfig"""
    pricing = get_user_pricing(request.user) if request.user.is_authenticated else None
    config = PricingConfig.get_config()
    
    # Pre-calculate all price variations for template
    price_vars = {
        'price_bw': float(config.admin_price_per_page),
        'price_bw_double': float(config.admin_price_per_page) + 0.20,
        'price_color': float(config.admin_price_per_page) + 6.50,
        'price_color_double': float(config.admin_price_per_page) + 11.50,
        'spiral_binding': float(config.spiral_binding_price_admin), # Legacy/Fallback
        'soft_binding': float(config.soft_binding_price_admin),
        'custom_base': float(config.custom_1_4_price_admin), # Fallback representation
    }
    
    context = {
        'services': Service.objects.all(),
        'locations': Location.objects.all(), # Dynamic Locations
        'pricing': pricing,
        'config': config,
        'price_vars': price_vars,
    }
    return render(request, 'core/services.html', context)
def about(request): return render(request, 'core/about.html')
def contact(request): return render(request, 'core/contact.html')
def privacy_policy(request): return render(request, 'core/privacy_policy.html')
def terms_conditions(request): return render(request, 'core/terms_conditions.html')

# --- 🏪 6. DEALER DASHBOARD ---
from functools import wraps
from datetime import datetime, timedelta
from django.db.models import Q

def dealer_required(view_func):
    """Decorator to ensure user is authenticated and is a dealer"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dealer_login')
        try:
            profile = request.user.profile
            if not profile.is_dealer:
                messages.error(request, "Access denied. Dealer privileges required.")
                return redirect('dealer_login')
        except UserProfile.DoesNotExist:
            messages.error(request, "Access denied. Dealer privileges required.")
            return redirect('dealer_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def dealer_login_view(request):
    if request.user.is_authenticated:
        try:
            if request.user.profile.is_dealer:
                return redirect('dealer_dashboard')
        except UserProfile.DoesNotExist:
            pass
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            try:
                if user.profile.is_dealer:
                    login(request, user)
                    return redirect('dealer_dashboard')
                else:
                    messages.error(request, "Access denied. This is a dealer-only portal.")
            except UserProfile.DoesNotExist:
                messages.error(request, "Access denied. Dealer profile not found.")
        else:
            messages.error(request, "Invalid credentials.")
    
    return render(request, 'dealer/dealer_login.html')

@dealer_required
def dealer_dashboard_view(request):
    # Get pricing for this dealer
    pricing = get_user_pricing(request.user)
    
    # Dealer Pricing Logic Helper
    def calculate_dealer_price(order):
        cost = 0.0
        pages = order.pages
        copies = order.copies
        
        # 1. Base Printing Cost
        if order.service_name == "Custom Printing":
            layout = order.print_mode or ""
            divisor = 1
            rate = 0.0
            
            if "1/4" in layout:
                divisor = 4
                rate = pricing['custom_1_4_price']
            elif "1/8" in layout:
                divisor = 8
                rate = pricing['custom_1_8_price']
            elif "1/9" in layout:
                divisor = 9
                rate = pricing['custom_1_9_price']
            else:
                divisor = 4
                rate = pricing['custom_1_4_price'] # Default
                
            sheets = -(-pages // divisor) # Ceiling division
            cost = sheets * rate * copies
            
        else:
            print_rate = pricing['price_per_page']
            if order.print_mode == 'color':
                print_rate += pricing['color_addition']
            
            base_print_cost = pages * copies * print_rate
            cost = base_print_cost

        # 2. Binding Costs
        if "Spiral" in order.service_name:
            binding_rate = 0
            t1 = pricing['spiral_tier1_limit']
            t2 = pricing['spiral_tier2_limit']
            t3 = pricing['spiral_tier3_limit']
            
            if pages <= t1:
                binding_rate = pricing['spiral_tier1_price']
            elif pages <= t2:
                binding_rate = pricing['spiral_tier2_price']
            elif pages <= t3:
                binding_rate = pricing['spiral_tier3_price']
            else:
                extra_pages = pages - t3
                steps = -(-extra_pages // 20) # Ceil
                binding_rate = pricing['spiral_tier3_price'] + (steps * pricing['spiral_extra_price'])
            
            cost += (binding_rate * copies)
            
        elif "Soft" in order.service_name:
            cost += (pricing['soft_binding'] * copies)
            
        return cost

    # Get filter parameters
    date_filter = request.GET.get('date_filter', 'all')
    status_filter = request.GET.get('status', 'all')
    service_filter = request.GET.get('service', 'all')
    
    # Base queryset
    orders = Order.objects.filter(payment_status='Success')
    
    # Filter by Dealer Assigned Locations
    if hasattr(request.user, 'profile') and request.user.profile.dealer_locations.exists():
        # Get names of all assigned locations
        loc_names = list(request.user.profile.dealer_locations.values_list('name', flat=True))
        if loc_names:
            orders = orders.filter(location__in=loc_names)
        else:
            orders = orders.none()
    else:
        # No profile or no locations assigned -> Show nothing
        orders = orders.none()
    
    # Apply date filter
    today = datetime.now().date()
    if date_filter == 'today':
        orders = orders.filter(created_at__date=today)
    elif date_filter == 'last_7_days':
        orders = orders.filter(created_at__date__gte=today - timedelta(days=7))
    elif date_filter == 'last_30_days':
        orders = orders.filter(created_at__date__gte=today - timedelta(days=30))
    
    # Apply status filter
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Apply service filter
    if service_filter != 'all':
        orders = orders.filter(service_name__icontains=service_filter)
    
    # Get orders for display (only Pending and Ready)
    display_orders = orders.filter(Q(status='Pending') | Q(status='Ready')).order_by('-created_at')
    
    # Add calculated amount to each order and sum revenue
    # Calculate Total Revenue (Items + Delivery) for ALL matching orders
    item_revenue = sum(calculate_dealer_price(o) for o in orders)
    unique_txns_count = orders.values('transaction_id').distinct().count()
    delivery_revenue = unique_txns_count * pricing['delivery_charge']
    
    total_revenue = item_revenue + delivery_revenue
    total_orders = orders.count()
    
    # Prepare Display Orders (Table view)
    final_display_orders = []
    for order in display_orders:
        order.dealer_amount = calculate_dealer_price(order)
        final_display_orders.append(order)
        
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'orders': final_display_orders,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'dealer_name': request.user.first_name or request.user.username,
    }
    
    return render(request, 'dealer/dealer_dashboard.html', context)


@dealer_required
def dealer_logout_view(request):
    logout(request)
    return redirect('dealer_login')

@dealer_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Only allow Pending and Ready status changes
        if new_status in ['Pending', 'Ready']:
            order.status = new_status
            order.save()
            messages.success(request, f"Order {order.order_id} status updated to {new_status}")
        else:
            messages.error(request, "Invalid status")
    
    return redirect('dealer_dashboard')

@dealer_required
def dealer_download_file(request, order_id):
    """Allow dealers to download order files"""
    from django.http import FileResponse, Http404
    import os
    
    order = get_object_or_404(Order, id=order_id, payment_status='Success')
    
    # Determine which file to download
    if order.document and order.document.name:
        file_field = order.document
        # Get actual extension from file
        _, ext = os.path.splitext(file_field.name)
        file_extension = ext if ext else ".pdf"
    elif order.image_upload and order.image_upload.name:
        file_field = order.image_upload
        # Get actual extension from file
        _, ext = os.path.splitext(file_field.name)
        file_extension = ext if ext else ".jpg"
    else:
        raise Http404("No file found for this order")
    
    # Check if file exists
    try:
        file_path = file_field.path
        if not os.path.exists(file_path):
            raise Http404(f"File does not exist: {file_field.name}")
    except Exception as e:
        raise Http404(f"Error accessing file: {str(e)}")
    
    # Generate a descriptive filename
    service_name = order.service_name.replace(" ", "_") if order.service_name else "Order"
    download_filename = f"{order.order_id}_{service_name}{file_extension}"
    
    # Return the file using FileResponse
    try:
        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=download_filename
        )
        return response
    except Exception as e:
        raise Http404(f"Error downloading file: {str(e)}")