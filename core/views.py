import io, uuid, PyPDF2, base64, json, requests, hashlib
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

from .models import Service, Order, UserProfile, CartItem

# --- 🚀 0. CORE LOGIC ENGINES (Success/Failure/Helper) ---



def handle_failed_order(user, items_list, txn_id, reason="Payment Failed"):
    """
    Atomically handles payment failure.
    1. Creates 'Cancelled' order records for history.
    2. STRICT ISOLATION: If it was a Direct Order (DIR prefix), 
       restores ONLY those items to the database CartItem table.
    """
    with transaction.atomic():
        last_order = None
        for item in items_list:
            if not item: 
                continue
                
            last_order = Order.objects.create(
                user=user,
                service_name=item.get('service_name'),
                total_price=float(item.get('total_price', 0)),
                location=item.get('location'),
                print_mode=item.get('print_mode'),
                side_type=item.get('side_type'),
                copies=item.get('copies'),
                custom_color_pages=item.get('custom_color_pages'),
                transaction_id=txn_id,
                payment_status="Failed",
                status="Cancelled"
            )
            
            # [STRICT REQUIREMENT] Restore to DB Cart only if it was a Direct Service-Page Order.
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
    Moves temp files to permanent Order records and clears temp storage.
    [ISOLATION RULE]: Only processes the items passed in items_list.
    [STATUS UPDATE]: Sets the initial order status to 'Pending' for admin review.
    """
    last_order = None
    with transaction.atomic():
        for item in items_list:
            if not item:
                continue
                
            saved_pdf, saved_img = None, None
            path = item.get('temp_path') or item.get('temp_image_path')
            
            if path and default_storage.exists(path):
                with default_storage.open(path) as f:
                    content = ContentFile(f.read(), name=item['document_name'])
                    if item.get('temp_path'):
                        saved_pdf = content
                    else:
                        saved_img = content
            
            # Create the permanent order record with status 'Pending'
            last_order = Order.objects.create(
                user=user, 
                service_name=item['service_name'], 
                total_price=float(item['total_price']),
                location=item['location'], 
                print_mode=item['print_mode'], 
                side_type=item['side_type'],
                copies=item['copies'], 
                custom_color_pages=item.get('custom_color_pages', ''),
                transaction_id=txn_id, 
                document=saved_pdf, 
                image_upload=saved_img,
                payment_status="Success", 
                status="Pending"  # Updated from 'Confirmed' to 'Pending'
            )
            
            # [CLEANUP] Delete temp files for these specific items
            if item.get('temp_path') and default_storage.exists(item['temp_path']):
                default_storage.delete(item['temp_path'])
            if item.get('temp_image_path') and default_storage.exists(item['temp_image_path']):
                default_storage.delete(item['temp_image_path'])
                
    return last_order

# --- 👤 1. AUTHENTICATION & PROFILE ---

def register_view(request):
    if request.user.is_authenticated: 
        return redirect('home')
        
    if request.method == "POST":
        full_name = request.POST.get('name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        address = request.POST.get('address', '').strip()

        # Validation
        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return redirect('register')

        # 1. Create the Base User (Stores Name and Email)
        user = User.objects.create_user(
            username=mobile, 
            password=password, 
            first_name=full_name,
            email=email
        )

        # 2. Create the User Profile (Stores Mobile and Address)
        # Note: fc_user_id is generated automatically in models.py
        UserProfile.objects.create(
            user=user, 
            mobile=mobile,
            address=address
        )

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
            db_items = CartItem.objects.filter(user=request.user)
            request.session['cart'] = [{
                'service_name': i.service_name, 'total_price': str(i.total_price), 'document_name': i.document_name,
                'temp_path': i.temp_path, 'temp_image_path': i.temp_image_path, 'copies': i.copies, 'pages': i.pages,
                'location': i.location, 'print_mode': i.print_mode, 'side_type': i.side_type, 'custom_color_pages': i.custom_color_pages
            } for i in db_items]
            return redirect('home')
        messages.error(request, "Invalid login credentials.")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request); return redirect('home')

@login_required(login_url='login')
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'profile': profile,
        'user_name': request.user.first_name,
        'user_email': request.user.email,
        'recent_bookings': orders[:5],
    }
    return render(request, 'core/profile.html', context)

@login_required(login_url='login')
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == "POST":
        # Get data from form
        new_name = request.POST.get('name')
        new_email = request.POST.get('email')
        new_mobile = request.POST.get('mobile')
        new_address = request.POST.get('address')

        # 1. Update Django Auth User table (Name & Email)
        request.user.first_name = new_name
        request.user.email = new_email
        # If mobile changes, username must also change to stay in sync
        request.user.username = new_mobile 
        request.user.save()

        # 2. Update UserProfile table (Mobile & Address)
        profile.mobile = new_mobile
        profile.address = new_address
        profile.save()

        messages.success(request, "Your profile details have been updated successfully!")
        return redirect('profile')
        
    return render(request, 'core/edit_profile.html', {'profile': profile})

@login_required(login_url='login')
def history_view(request):
    """
    MASTER TRANSACTION LOG:
    Fetches all orders associated with the logged-in user.
    Ordered by '-created_at' to show the most recent activity at the top.
    Includes filtering for Pending, Success, and Cancelled states.
    """
    # 1. Fetch all orders for the user
    all_orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # 2. Context metadata for the UI
    context = {
        'orders': all_orders,
        'total_orders_count': all_orders.count(),
        # Optimization: Only count active/pending orders for a "Processing" badge if needed
        'active_count': all_orders.filter(status__in=['Pending', 'Confirmed', 'Ready']).count(),
    }

    return render(request, 'core/history.html', context)

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
        page_count = int(request.POST.get('page_count', 1))
        file_path = default_storage.save(f'temp/{uuid.uuid4()}_{uploaded_file.name}', ContentFile(uploaded_file.read()))
        
        service_name = request.POST.get('service_name')
        print_mode = request.POST.get('print_mode', 'B&W')
        layout = request.POST.get('layout_type')
        if service_name == "Custom Printing" and layout:
            print_mode = f"{print_mode}({layout})"

        item = {
            'service_name': service_name, 'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name, 'temp_path': file_path if uploaded_file.name.endswith('.pdf') else None,
            'temp_image_path': file_path if not uploaded_file.name.endswith('.pdf') else None, 
            'copies': int(request.POST.get('copies', 1)), 'pages': page_count, 'location': request.POST.get('location'),
            'print_mode': print_mode, 'side_type': request.POST.get('side_type', 'single'),
            'custom_color_pages': request.POST.get('custom_color_pages', ''),
        }
        CartItem.objects.create(user=request.user, **item)
        cart = request.session.get('cart', []); cart.append(item); request.session['cart'] = cart; request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=401)

@login_required(login_url='login')
def cart_page(request):
    """
    DATABASE-FIRST CART VIEW:
    Fetches directly from the CartItem table to ensure 100% sync
    with failed-payment restorations.
    """
    # 1. Fetch from Database (This is the fix)
    db_items = CartItem.objects.filter(user=request.user).order_by('-created_at')
    
    # 2. Sync the session so the Navbar count is correct
    cart_list = []
    for i in db_items:
        cart_list.append({
            'service_name': i.service_name,
            'total_price': str(i.total_price),
            'document_name': i.document_name,
            'temp_path': i.temp_path,
            'temp_image_path': i.temp_image_path,
            'copies': i.copies,
            'pages': i.pages,
            'location': i.location,
            'print_mode': i.print_mode,
            'side_type': i.side_type,
            'custom_color_pages': i.custom_color_pages,
        })
    request.session['cart'] = cart_list
    request.session.modified = True

    # 3. Calculate Totals
    total_bill = sum(float(i.total_price) for i in db_items)
    total_eff_pages = sum(int(i.pages) * int(i.copies) for i in db_items)

    context = {
        'cart_items': cart_list, 
        'total_bill': round(total_bill, 2),
        'total_pages': total_eff_pages,
        'min_required': 5,
        'remaining_pages': max(0, 5 - total_eff_pages)
    }
    return render(request, 'core/cart.html', context)

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart = request.session.get('cart', [])
    if 0 <= item_id < len(cart):
        item = cart.pop(item_id)
        CartItem.objects.filter(user=request.user, document_name=item.get('document_name')).delete()
        request.session['cart'] = cart; request.session.modified = True
    return redirect('cart')

# --- 🚀 3. ORDER & CHECKOUT FLOW ---

@login_required(login_url='login')
def order_all(request):
    cart = request.session.get('cart', [])
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
    # Isolation: Ensure direct item session is cleared when checking out from cart
    if 'direct_item' in request.session:
        del request.session['direct_item']
    request.session['pending_batch_id'] = f"TXN_{uuid.uuid4().hex[:10].upper()}"
    request.session.modified = True
    return redirect('cart_checkout_summary')

@login_required(login_url='login')
def order_now(request):
    """Path for SERVICE PAGE item only. Ignores Cart."""
    if request.method == "POST":
        uploaded_file = request.FILES.get('document')
        if not uploaded_file: return redirect('services')
        file_path = default_storage.save(f'temp/direct_{uuid.uuid4()}_{uploaded_file.name}', ContentFile(uploaded_file.read()))
        service_name = request.POST.get('service_name')
        print_mode = request.POST.get('print_mode', 'B&W')
        layout = request.POST.get('layout_type')
        if service_name == "Custom Printing" and layout:
            print_mode = f"{print_mode}({layout})"

        request.session['direct_item'] = {
            'service_name': service_name, 'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name, 'temp_path': file_path if uploaded_file.name.endswith('.pdf') else None,
            'temp_image_path': file_path if not uploaded_file.name.endswith('.pdf') else None, 
            'copies': int(request.POST.get('copies', 1)), 'pages': int(request.POST.get('page_count', 1)), 
            'location': request.POST.get('location'), 'print_mode': print_mode, 
            'side_type': request.POST.get('side_type', 'single'), 'custom_color_pages': request.POST.get('custom_color_pages', ''),
        }
        # Mark as Direct Order with DIR_ prefix
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
        service_name = request.POST.get('service_name')
        print_mode = request.POST.get('print_mode', 'B&W')
        layout = request.POST.get('layout_type')
        if service_name == "Custom Printing" and layout:
            print_mode = f"{print_mode}({layout})"

        direct_item = {
            'service_name': service_name, 'total_price': request.POST.get('total_price_hidden'),
            'document_name': uploaded_file.name, 'temp_path': file_path if uploaded_file.name.endswith('.pdf') else None,
            'temp_image_path': file_path if not uploaded_file.name.endswith('.pdf') else None, 
            'copies': int(request.POST.get('copies', 1)), 'pages': int(request.POST.get('page_count', 1)), 
            'location': request.POST.get('location'), 'print_mode': print_mode, 
            'side_type': request.POST.get('side_type', 'single'), 'custom_color_pages': request.POST.get('custom_color_pages', ''),
        }
        request.session['direct_item'] = direct_item
        request.session['pending_batch_id'] = f"DIR_{uuid.uuid4().hex[:10].upper()}"
        request.session.modified = True
        return JsonResponse({'success': True, 'redirect_url': '/checkout/summary/'})
    return JsonResponse({'success': False})

@login_required(login_url='login')
def cart_checkout_summary(request):
    """STRICT FILTER: Checks prefix to choose between Cart and Direct item."""
    batch_txn_id = request.session.get('pending_batch_id', '')
    direct_item = request.session.get('direct_item')
    if batch_txn_id.startswith("DIR"):
        items = [direct_item] if direct_item else []
    else:
        items = request.session.get('cart', [])
        
    if not items or None in items: return redirect('services')
    grand_total = sum(float(i.get('total_price', 0)) for i in items)
    return render(request, 'core/checkout.html', {'cart_items': items, 'grand_total': round(grand_total, 2), 'items_count': len(items)})

# --- 💳 4. PHONEPE GATEWAY INTEGRATION ---



@login_required(login_url='login')
def initiate_payment(request):
    """
    STRICT ISOLATION & PERSISTENCE:
    1. Identifies source (Direct vs Cart) via batch_txn_id prefix.
    2. For DIRECT orders: Automatically adds to DB Cart BEFORE payment to handle "Back" or "Close Tab" scenarios.
    3. Records Pending Order in DB for history tracking.
    4. Redirects to PhonePe gateway.
    """
    batch_txn_id = request.session.get('pending_batch_id')
    direct_item = request.session.get('direct_item')
    cart_items = request.session.get('cart', [])

    if not batch_txn_id: 
        return redirect('cart')

    # --- 🛡️ THE ISOLATION & FAIL-SAFE TRANSFER FILTER ---
    if batch_txn_id.startswith("DIR"):
        # Source: Service Page (Order Now)
        items_to_process = [direct_item] if direct_item else []
        
        # PRE-EMPTIVE BACKUP: Add to DB Cart immediately.
        # This covers the "Back" button or "Close Window" scenario.
        if direct_item:
            CartItem.objects.get_or_create(
                user=request.user,
                document_name=direct_item.get('document_name'),
                defaults={
                    'service_name': direct_item.get('service_name'),
                    'total_price': direct_item.get('total_price'),
                    'temp_path': direct_item.get('temp_path'),
                    'temp_image_path': direct_item.get('temp_image_path'),
                    'copies': direct_item.get('copies'),
                    'pages': direct_item.get('pages', 1),
                    'location': direct_item.get('location'),
                    'print_mode': direct_item.get('print_mode'),
                    'side_type': direct_item.get('side_type'),
                    'custom_color_pages': direct_item.get('custom_color_pages')
                }
            )
    else:
        # Source: Cart Page (Order All)
        items_to_process = cart_items

    if not items_to_process or None in items_to_process:
        messages.error(request, "No items found for this order session.")
        return redirect('cart')

    # --- 🏦 DATABASE: Pre-record 'Pending' Orders ---
    with transaction.atomic():
        for item in items_to_process:
            Order.objects.update_or_create(
                transaction_id=batch_txn_id, 
                document=item.get('document_name'),
                defaults={
                    'user': request.user, 
                    'service_name': item.get('service_name'),
                    'total_price': float(item.get('total_price', 0)), 
                    'location': item.get('location'),
                    'print_mode': item.get('print_mode'), 
                    'side_type': item.get('side_type'),
                    'copies': item.get('copies'), 
                    'custom_color_pages': item.get('custom_color_pages', ''),
                    'payment_status': "Pending", 
                    'status': "Pending"
                }
            )

    # --- 💳 PHONEPE API: Handshake ---
    grand_total = sum(float(i.get('total_price', 0)) for i in items_to_process)
    amount_paisa = int(grand_total * 100)
    callback_url = f"{request.scheme}://{request.get_host()}/payment/callback/"

    payload = {
        "merchantId": settings.PHONEPE_MERCHANT_ID,
        "merchantTransactionId": batch_txn_id,
        "merchantUserId": f"U{request.user.id}",
        "amount": amount_paisa,
        "redirectUrl": callback_url,
        "redirectMode": "POST",
        "callbackUrl": callback_url,
        "paymentInstrument": {"type": "PAY_PAGE"}
    }

    base64_payload = base64.b64encode(json.dumps(payload).encode()).decode()
    verify_str = base64_payload + "/pg/v1/pay" + settings.PHONEPE_SALT_KEY
    checksum = hashlib.sha256(verify_str.encode()).hexdigest() + "###" + settings.PHONEPE_SALT_INDEX

    headers = {"Content-Type": "application/json", "X-VERIFY": checksum, "accept": "application/json"}
    
    try:
        response = requests.post(settings.PHONEPE_API_URL, json={"request": base64_payload}, headers=headers)
        res_json = response.json()
        if res_json.get('success'):
            return redirect(res_json['data']['instrumentResponse']['redirectInfo']['url'])
        else:
            Order.objects.filter(transaction_id=batch_txn_id).update(payment_status="Failed", status="Cancelled")
            return redirect('cart')
    except Exception:
        return redirect('cart')

@login_required(login_url='login')
def bypass_payment(request):
    """
    TEST MODE: Simulates a successful transaction with strict source isolation.
    1. Detects source via 'pending_batch_id' prefix (DIR_ vs TXN_).
    2. Finalizes the order records in the database with 'Pending' status.
    3. Performs surgical cleanup:
       - If Direct: Clears only the temporary session and the DB backup for that specific item.
       - If Cart: Clears the entire session and DB cart.
    """
    txn_id = request.session.get('pending_batch_id')
    direct_item = request.session.get('direct_item')
    
    # --- 1. Identify Target Items ---
    if txn_id and txn_id.startswith("DIR"):
        # Source: Service Page (Order Now)
        items = [direct_item] if direct_item else []
    else:
        # Source: Cart Page (Order All)
        items = request.session.get('cart', [])

    # Validation check
    if not items or None in items:
        messages.error(request, "No items found to process for this test.")
        return redirect('cart')

    # --- 2. Database Finalization ---
    # process_successful_order moves files and sets status to 'Pending'
    last_o = process_successful_order(request.user, items, txn_id)
    
    # --- 3. Surgical Cleanup ---
    if txn_id.startswith("DIR"):
        # Success Cleanup for Direct Order:
        # Remove the pre-emptive DB backup created in initiate_payment
        if direct_item:
            CartItem.objects.filter(
                user=request.user, 
                document_name=direct_item.get('document_name')
            ).delete()
        
        # Remove the temporary service-page session item
        if 'direct_item' in request.session: 
            del request.session['direct_item']
    else:
        # Success Cleanup for Cart Order:
        # Wipe the entire persistent cart and session
        request.session['cart'] = []
        CartItem.objects.filter(user=request.user).delete()
        
    # Commit session changes
    request.session.modified = True
    
    messages.success(request, f"Test Payment Successful! Order {last_o.order_id} is now Pending.")
    return render(request, 'core/payment_success.html', {'order': last_o})

from django.contrib import messages

@csrf_exempt
def payment_callback(request):
    """
    STRICT CALLBACK: Handles failure, triggers flash message, and syncs cart.
    """
    txn_id = request.POST.get('merchantTransactionId', '')
    code = request.POST.get('code', '')
    
    direct_item = request.session.get('direct_item')
    is_direct = txn_id.startswith("DIR") if txn_id else False
    items_involved = [direct_item] if is_direct else request.session.get('cart', [])

    if code == 'PAYMENT_SUCCESS':
        process_successful_order(request.user, items_involved, txn_id)
        # ... (Success cleanup logic) ...
        messages.success(request, "Order placed successfully!")
        return redirect('history')
    else:
        # --- ❌ FAILURE CASE ---
        handle_failed_order(request.user, items_involved, txn_id)
        
        # 1. SET THE MESSAGE: This is what you were missing
        messages.error(
            request, 
            "PAYMENT FAILED: Your transaction could not be completed. Your items are safe in the cart."
        )
        
        if is_direct and direct_item:
            # Move to DB Cart
            CartItem.objects.get_or_create(
                user=request.user,
                document_name=direct_item.get('document_name'),
                defaults=direct_item
            )
            # Sync Session so UI updates
            db_cart = CartItem.objects.filter(user=request.user)
            request.session['cart'] = [{k: str(v) if k == 'total_price' else v for k, v in i.__dict__.items() if not k.startswith('_')} for i in db_cart]
            if 'direct_item' in request.session:
                del request.session['direct_item']

        # 2. FORCE SAVE: Ensures the message is written to the DB/Cookie before redirect
        request.session.modified = True
        request.session.save() 
        
        return redirect('cart')
    
# --- 🌐 5. STATIC PAGES ---
def home(request): return render(request, 'core/index.html', {'services': Service.objects.all()[:3]})
def services_page(request): return render(request, 'core/services.html', {'services': Service.objects.all()})
def about(request): return render(request, 'core/about.html')
def contact(request): return render(request, 'core/contact.html')
def privacy_policy(request): return render(request, 'core/privacy_policy.html')
def terms_conditions(request): return render(request, 'core/terms_conditions.html')