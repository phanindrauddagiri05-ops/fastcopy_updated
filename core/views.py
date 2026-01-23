import io, uuid, PyPDF2, base64, json, requests, hashlib, time, os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from functools import wraps
from datetime import datetime, timedelta
from django.db.models import Q, Sum, Count

from django.utils import timezone
from .models import Service, Order, UserProfile, CartItem, PricingConfig, Location, Coupon, PopupOffer, MaintenanceSettings
from .utils import calculate_delivery_date
from .notifications import send_all_order_notifications

# --- 🚀 0. CORE LOGIC ENGINES (Success/Failure/Helper) ---

def get_user_pricing(user):
    """
    Get appropriate pricing configuration based on user type.
    Returns dict with all prices for the specific user (dealer vs regular).
    """
    config = PricingConfig.get_config()
    
    # Check if user is a dealer
    try:
        profile = user.profile
        is_dealer = profile.is_dealer
    except:
        is_dealer = False
    
    base_dict = {
        # Single-sided pricing
        'price_per_page': float(config.dealer_price_per_page) if is_dealer else float(config.admin_price_per_page),
        # Double-sided pricing
        'price_per_page_double': float(config.dealer_price_per_page_double) if is_dealer else float(config.admin_price_per_page_double),
        
        'soft_binding': float(config.soft_binding_price_dealer) if is_dealer else float(config.soft_binding_price_admin),
        
        # Single-sided color addition
        'color_addition': float(config.color_price_addition_dealer) if is_dealer else float(config.color_price_addition_admin),
        # Double-sided color addition
        'color_addition_double': float(config.color_price_addition_dealer_double) if is_dealer else float(config.color_price_addition_admin_double),
        
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
        'custom_1_8_price_double': float(config.custom_1_8_price_double_dealer) if is_dealer else float(config.custom_1_8_price_double_admin),
        'custom_1_9_price_double': float(config.custom_1_9_price_double_dealer) if is_dealer else float(config.custom_1_9_price_double_admin),
        'delivery_charge': float(config.delivery_price_dealer) if is_dealer else float(config.delivery_price_admin),
    }
    return base_dict

def handle_failed_order(user, txn_id, reason="Payment Failed"):
    """
    DATABASE UPDATE LOGIC:
    Targets specific records by txn_id to update statuses.
    Ensures 'Failed' and 'Cancelled' reflect in the database.
    Now resilient to session loss (doesn't require items_list).
    """
    if not txn_id:
        return None

    with transaction.atomic():
        # Clean up any potential duplicates or extra queries by filtering strictly
        db_orders = Order.objects.filter(transaction_id=txn_id)
        last_order = None
        
        for order in db_orders:
            # Update status
            order.payment_status = "Failed"
            order.status = "Cancelled"
            order.save()
            last_order = order
            
            # [ENHANCED] Restore to DB Cart for ALL cancelled/failed orders
            # This allows the user to try again easily
            # We use the order details to reconstruct the cart item
            CartItem.objects.get_or_create(
                user=user,
                service_name=order.service_name,
                document_name=order.document.name.split('/')[-1] if order.document else (order.image_upload.name.split('/')[-1] if order.image_upload else "Restored Document"),
                defaults={
                    'total_price': order.total_price,
                    # Note: We can't easily recover the original temp_path if it was deleted, 
                    # but if the file is in Order.document, we might strictly not need temp_path for valid cart items if logic handles it.
                    # ideally we rely on the file being present.
                    'copies': order.copies,
                    'pages': order.pages,
                    'location': order.location,
                    'print_mode': order.print_mode,
                    'side_type': order.side_type,
                    'custom_color_pages': order.custom_color_pages
                }
            )
        return last_order

def cleanup_payment_session(request):
    """
    Clean up all payment-related session variables.
    Called after both successful and failed payment attempts.
    """
    session_keys = [
        'pending_batch_id',
        'cashfree_payment_session_id', 
        'cashfree_order_id',
        'payment_return_url'
    ]
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    request.session.modified = True

def process_successful_order(user, txn_id):
    """
    DATABASE UPDATE LOGIC:
    Updates records to 'Success' and 'Pending' (for admin processing).
    Now simplified to iterate DB records directly, ensuring no session dependency.
    """
    with transaction.atomic():
        db_orders = Order.objects.filter(transaction_id=txn_id)
        
        for order in db_orders:
            # Critical: user might have changed if we recovered from session loss
            order.user = user 
            order.payment_status = "Success"
            order.status = "Pending"
            order.save()
            
            # Note: File saving is now done in initiate_payment to allow early handling.
            # We don't need to move files here anymore.
            
            # Cleanup temp files if possible/known (optional, low priority compared to reliability)

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

        confirm_password = request.POST.get('confirm_password', '')

        if not request.POST.get('terms_accepted'):
            messages.error(request, "You must accept the Terms and Conditions and Privacy Policy.")
            return redirect('register')
            
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
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
            return redirect('home') 
        messages.error(request, "Invalid login credentials.")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request); return redirect('home')

# --- 🔐 FORGOT PASSWORD VIEWS ---

def forgot_password_request(request):
    """Step 1: User enters mobile number to request password reset"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        mobile = request.POST.get('mobile', '').strip()
        
        if not mobile:
            messages.error(request, "Please enter your mobile number.")
            return render(request, 'core/forgot_password.html')
        
        try:
            user = User.objects.get(username=mobile)
            
            if not user.email:
                messages.error(request, "No email address is associated with this account. Please contact support.")
                return render(request, 'core/forgot_password.html')
            
            # Generate password reset token
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            reset_url = f"{request.scheme}://{request.get_host()}/password-reset/{uid}/{token}/"
            
            # Send email
            subject = "Reset Your FastCopy Password"
            message = render_to_string('core/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'company_name': getattr(settings, 'COMPANY_NAME', 'FastCopy'),
            })
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=message,
                    fail_silently=False,
                )
                messages.success(request, f"Password reset link sent to your registered email ({user.email[:3]}***{user.email[-10:]}).")
                return redirect('forgot_password_sent')
            except Exception as e:
                messages.error(request, "Failed to send email. Please try again later.")
                return render(request, 'core/forgot_password.html')
                
        except User.DoesNotExist:
            # Don't reveal if mobile exists or not (security)
            messages.error(request, "If this mobile number is registered, you will receive a password reset email.")
            return redirect('forgot_password_sent')
    
    return render(request, 'core/forgot_password.html')

def forgot_password_sent(request):
    """Step 2: Confirmation page after sending reset email"""
    return render(request, 'core/forgot_password_sent.html')

def password_reset_confirm(request, uidb64, token):
    """Step 3: User clicks reset link and sets new password"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password or len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'core/password_reset_confirm.html', {'valid_link': True})
            
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'core/password_reset_confirm.html', {'valid_link': True})
            
            user.set_password(new_password)
            user.save()
            messages.success(request, "Your password has been reset successfully! You can now login.")
            return redirect('password_reset_complete')
        
        return render(request, 'core/password_reset_confirm.html', {'valid_link': True})
    else:
        return render(request, 'core/password_reset_confirm.html', {'valid_link': False})

def password_reset_complete(request):
    """Step 4: Password reset success page"""
    return render(request, 'core/password_reset_complete.html')

@login_required(login_url='login')
def profile_view(request):
    """
    Profile View: Rectified to include live order tracking for the dashboard.
    Fetches the latest active (non-delivered) successful order for the tracker.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # NEW FEATURE: Fetch the most recent active order for the Live Tracker
    # We look for successful payments that are NOT yet delivered
    tracking = Order.objects.filter(
        user=request.user, 
        payment_status='Success'
    ).exclude(status__in=['Delivered', 'Rejected', 'Cancelled']).order_by('-created_at').first()
    
    context = {
        'profile': profile, 
        'user_name': request.user.first_name, 
        'user_email': request.user.email, 
        'recent_bookings': orders[:5],
        'tracking': tracking  # Passed to profile.html for the Active Tracking box
    }
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
def change_password(request):
    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect!")
            return redirect('change_password')
        
        # Validate new password match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match!")
            return redirect('change_password')
        
        # Validate password length
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long!")
            return redirect('change_password')
        
        # Validate password is different from current
        if current_password == new_password:
            messages.error(request, "New password must be different from current password!")
            return redirect('change_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Re-authenticate user to keep them logged in
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, "Password changed successfully!")
        return redirect('profile')
    
    return render(request, 'core/change_password.html')


@login_required(login_url='login')
def history_view(request):
    all_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/history.html', {'orders': all_orders})

# --- 🛒 2. CART & PDF ENGINE ---

def calculate_pages(request):
    """
    Optimized page counter.
    1. Tries PyMuPDF (fitz) - Extremely fast, handles large files instantly.
    2. Falls back to PyPDF2 (Optimized) - Reads stream directly without loading full file to RAM.
    """
    if request.method == 'POST' and request.FILES.get('document'):
        uploaded_file = request.FILES['document']
        
        # [OPTIMIZATION] Save file immediately to avoid re-upload later
        # We need to serve this path back to frontend
        unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
        temp_path = default_storage.save(f'temp/pre_{unique_filename}', ContentFile(uploaded_file.read()))
        
        # Reset pointer for reading
        uploaded_file.seek(0)
        
        # METHOD 1: PyMuPDF (Fastest)
        try:
            import fitz  # PyMuPDF
            # Open directly from the uploaded file buffer
            # Note: fitz.open can also take the file path we just saved, which might be even safer?
            # But stream is fine since we have it in memory right now.
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            page_count = doc.page_count
            doc.close()
            return JsonResponse({'success': True, 'pages': page_count, 'temp_path': temp_path})
        except ImportError:
            # PyMuPDF not installed, falling back...
            uploaded_file.seek(0) # Reset
            pass
        except Exception as e:
            print(f"PyMuPDF Error: {e}")
            uploaded_file.seek(0) # Reset
            pass

        # METHOD 2: PyPDF2 (Optimized Fallback)
        try:
            import PyPDF2
            # Reset file pointer to beginning after previous read attempt
            uploaded_file.seek(0)
            
            # CRITICAL OPTIMIZATION: Pass the file object directly.
            # Do NOT use io.BytesIO(uploaded_file.read()) as it doubles memory usage.
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            
            # Check for encryption
            if pdf_reader.is_encrypted:
                return JsonResponse({'success': False, 'error': 'File is encrypted'})
                
            return JsonResponse({'success': True, 'pages': len(pdf_reader.pages), 'temp_path': temp_path})
        except Exception as e:
            print(f"PyPDF2 Error: {e}")
            return JsonResponse({'success': False, 'error': 'Invalid PDF file'})
            
    return JsonResponse({'success': False})

def add_to_cart(request):
    if request.method == "POST" and request.user.is_authenticated:
        # Check if we have a pre-uploaded file path
        temp_doc_path = request.POST.get('temp_doc_path')
        file_path = None
        doc_name = "Unknown Document"
        is_pdf = True
        
        if temp_doc_path and default_storage.exists(temp_doc_path):
            # Use pre-uploaded file
            file_path = temp_doc_path
            doc_name = temp_doc_path.split('_', 2)[-1] # Attempt to extract original name
            if not doc_name: doc_name = "Document.pdf"
            is_pdf = doc_name.lower().endswith('.pdf')
        else:
            # Fallback to standard upload
            uploaded_file = request.FILES.get('document')
            if not uploaded_file: return JsonResponse({'success': False})
            doc_name = uploaded_file.name
            file_path = default_storage.save(f'temp/{uuid.uuid4()}_{doc_name}', ContentFile(uploaded_file.read()))
            is_pdf = doc_name.lower().endswith('.pdf')

        service_name = request.POST.get('service_name')
        print_mode = request.POST.get('print_mode', 'B&W')
        item = {
            'service_name': service_name, 'total_price': request.POST.get('total_price_hidden'),
            'document_name': doc_name, 
            'temp_path': file_path if is_pdf else None,
            'temp_image_path': file_path if not is_pdf else None, 
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
        # Check if we have a pre-uploaded file path
        temp_doc_path = request.POST.get('temp_doc_path')
        file_path = None
        doc_name = "Unknown Document"
        is_pdf = True
        
        if temp_doc_path and default_storage.exists(temp_doc_path):
            # Use pre-uploaded file
            file_path = temp_doc_path
            doc_name = temp_doc_path.split('_', 2)[-1]
            if not doc_name: doc_name = "Document.pdf"
            is_pdf = doc_name.lower().endswith('.pdf')
        else:
            uploaded_file = request.FILES.get('document')
            if not uploaded_file: return redirect('services')
            doc_name = uploaded_file.name
            file_path = default_storage.save(f'temp/direct_{uuid.uuid4()}_{doc_name}', ContentFile(uploaded_file.read()))
            is_pdf = doc_name.lower().endswith('.pdf')

        request.session['direct_item'] = {
            'service_name': request.POST.get('service_name'), 'total_price': request.POST.get('total_price_hidden'),
            'document_name': doc_name, 
            'temp_path': file_path if is_pdf else None,
            'temp_image_path': file_path if not is_pdf else None, 
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
    
    # Calculate original total
    items_total = sum(float(i.get('total_price', 0)) for i in items)
    pricing = get_user_pricing(request.user)
    delivery_charge = pricing.get('delivery_charge', 0.0)
    grand_total = items_total + delivery_charge
    
    # Handle coupon application
    coupon_code = request.session.get('applied_coupon_code')
    discount_amount = 0
    coupon_message = None
    coupon_valid = False
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper())
            can_apply, message = coupon.can_apply_to_order(grand_total)
            
            if can_apply:
                discount_amount, discount_message = coupon.calculate_discount(grand_total)
                grand_total -= discount_amount
                coupon_valid = True
                coupon_message = f"Coupon '{coupon_code}' applied successfully!"
            else:
                # Coupon no longer valid, remove from session
                del request.session['applied_coupon_code']
                request.session.modified = True
                coupon_message = message
                coupon_code = None
        except Coupon.DoesNotExist:
            # Coupon doesn't exist, remove from session
            del request.session['applied_coupon_code']
            request.session.modified = True
            coupon_code = None
    
    est_date = calculate_delivery_date()
    
    context = {
        'cart_items': items, 
        'grand_total': round(grand_total, 2),
        'original_total': round(items_total + delivery_charge, 2),
        'items_count': len(items),
        'delivery_charge': delivery_charge,
        'est_delivery_date': est_date,
        'total_pages': sum(int(i.get('pages', 1)) * int(i.get('copies', 1)) for i in items),
        'coupon_code': coupon_code,
        'discount_amount': round(discount_amount, 2),
        'coupon_valid': coupon_valid,
        'coupon_message': coupon_message,
    }
    
    return render(request, 'core/checkout.html', context)


# --- 🎟️ 3A. COUPON MANAGEMENT ---

@login_required(login_url='login')
def apply_coupon(request):
    """AJAX view to apply a coupon code"""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Invalid request method'})
        
        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        
        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})
        
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code'})
        
        # Calculate current order total
        batch_txn_id = request.session.get('pending_batch_id', '')
        if batch_txn_id.startswith("DIR"):
            items = [request.session.get('direct_item')] if request.session.get('direct_item') else []
        else:
            items = request.session.get('cart', [])
        
        if not items:
            return JsonResponse({'success': False, 'message': 'Your cart is empty'})
        
        items_total = sum(float(i.get('total_price', 0)) for i in items)
        pricing = get_user_pricing(request.user)
        delivery_charge = pricing.get('delivery_charge', 0.0)
        grand_total = items_total + delivery_charge
        
        # Validate coupon
        can_apply, message = coupon.can_apply_to_order(grand_total)
        
        if not can_apply:
            return JsonResponse({'success': False, 'message': message})
        
        # Calculate discount
        discount_amount, discount_message = coupon.calculate_discount(grand_total)
        final_total = grand_total - discount_amount
        
        # Save to session
        request.session['applied_coupon_code'] = coupon_code
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': f'Coupon applied! You saved ₹{discount_amount:.2f}',
            'coupon_code': coupon_code,
            'discount_amount': round(discount_amount, 2),
            'discount_percentage': float(coupon.discount_percentage),
            'original_total': round(grand_total, 2),
            'final_total': round(final_total, 2)
        })
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in apply_coupon: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'})



@login_required(login_url='login')
def remove_coupon(request):
    """AJAX view to remove applied coupon"""
    if request.method == 'POST':
        if 'applied_coupon_code' in request.session:
            del request.session['applied_coupon_code']
            request.session.modified = True
        
        #Calculate total without coupon
        batch_txn_id = request.session.get('pending_batch_id', '')
        if batch_txn_id.startswith("DIR"):
            items = [request.session.get('direct_item')] if request.session.get('direct_item') else []
        else:
            items = request.session.get('cart', [])
        
        items_total = sum(float(i.get('total_price', 0)) for i in items) if items else 0
        pricing = get_user_pricing(request.user)
        delivery_charge = pricing.get('delivery_charge', 0.0)
        grand_total = items_total + delivery_charge
        
        return JsonResponse({
            'success': True,
            'message': 'Coupon removed',
            'grand_total': round(grand_total, 2)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


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
    est_date = calculate_delivery_date()
    
    # Calculate totals and handle coupon
    items_total = sum(float(i.get('total_price', 0)) for i in items_to_process)
    pricing = get_user_pricing(request.user)
    delivery_charge = pricing.get('delivery_charge', 0.0)
    original_total = items_total + delivery_charge
    
    # Apply coupon if available
    applied_coupon_code = request.session.get('applied_coupon_code')
    discount_amount = 0
    coupon_obj = None
    
    if applied_coupon_code:
        try:
            coupon_obj = Coupon.objects.get(code=applied_coupon_code.upper())
            can_apply, message = coupon_obj.can_apply_to_order(original_total)
            if can_apply:
                discount_amount, _ = coupon_obj.calculate_discount(original_total)
        except Coupon.DoesNotExist:
            pass
    
    final_total = original_total - discount_amount
    
    final_total = original_total - discount_amount
    
    with transaction.atomic():
        for item in items_to_process:
            # Create the order object
            order_obj = Order.objects.create(
                transaction_id=unique_order_id, 
                user=request.user,
                service_name=item.get('service_name'),
                total_price=float(item.get('total_price', 0)), 
                original_price=original_total if applied_coupon_code else None,
                coupon_code=applied_coupon_code if applied_coupon_code else None,
                discount_amount=discount_amount if discount_amount > 0 else 0,
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

            # [CRITICAL] SAVE FILE IMMEDIATELY
            # We intentionally duplicate the file from temp to the Order object NOW.
            # This ensures that even if the session is lost during payment (which holds the temp_path),
            # the Order has the file physically attached.
            try:
                path = item.get('temp_path') or item.get('temp_image_path')
                if path and default_storage.exists(path):
                    with default_storage.open(path) as f:
                        file_content = ContentFile(f.read(), name=item.get('document_name'))
                        if item.get('temp_path'):
                            order_obj.document.save(item.get('document_name'), file_content, save=True)
                        else:
                            order_obj.image_upload.save(item.get('document_name'), file_content, save=True)
            except Exception as e:
                print(f"⚠️ Error attaching file to order at init: {e}")
                # Continue anyway, don't block payment. We might recover later or manual intervention.
        
        # Increment coupon usage if applied
        if coupon_obj and discount_amount > 0:
            coupon_obj.increment_usage()
            # Clear coupon from session after use
            if 'applied_coupon_code' in request.session:
                del request.session['applied_coupon_code']
                request.session.modified = True
    
    
    # Cashfree URL Handling
    # Cashfree Production requires HTTPS for return_url in the API.
    # We use a dummy HTTPS URL for the API validation, but the Frontend SDK will use 'payment_return_url' session var to redirect correctly.
    current_host = request.get_host()
    if 'localhost' in current_host or '127.0.0.1' in current_host:
        return_url_for_api = "https://www.cashfree.com/return" # Dummy HTTPS
        actual_return_url = f"http://{current_host}/payment/callback/"
    else:
        # Production/HTTPS
        return_url_for_api = f"https://{current_host}/payment/callback/?order_id={unique_order_id}"
        actual_return_url = f"https://{current_host}/payment/callback/"
    
    user_mobile = request.user.profile.mobile if hasattr(request.user, 'profile') else "9999999999"
    if not user_mobile.startswith('91'): user_mobile = f"91{user_mobile}"

    payload = {
        "order_id": unique_order_id,
        "order_amount": float(final_total),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": f"CUST_{request.user.id}",
            "customer_name": request.user.username,
            "customer_email": request.user.email or "test@fastcopy.in",
            "customer_phone": user_mobile
        },
        "order_meta": {
            "return_url": return_url_for_api
        }
    }
    headers = {"Content-Type": "application/json", "x-api-version": settings.CASHFREE_API_VERSION, "x-client-id": settings.CASHFREE_APP_ID, "x-client-secret": settings.CASHFREE_SECRET_KEY}
    
    # Debug logging
    print(f"=== Cashfree Payment Initiation ===")
    print(f"Order ID: {unique_order_id}")
    print(f"Amount: {final_total}")
    print(f"Return URL (API): {return_url_for_api}")
    
    # Store the actual return URL in session for frontend to use
    request.session['payment_return_url'] = actual_return_url
    request.session.modified = True
    
    try:
        response = requests.post(f"{settings.CASHFREE_API_URL}/orders", json=payload, headers=headers, timeout=10)
        res_json = response.json()
        
        # Log the response for debugging
        print(f"Cashfree API Response Status: {response.status_code}")
        
        if response.status_code == 200 and res_json.get('payment_session_id'):
            request.session['cashfree_payment_session_id'] = res_json.get('payment_session_id')
            request.session['cashfree_order_id'] = unique_order_id
            request.session.modified = True
            return redirect('cashfree_checkout')
        else:
            # API call failed, show error message
            error_msg = res_json.get('message', 'Payment gateway error')
            print(f"Cashfree Error: {error_msg}")
            messages.error(request, f"Payment initiation failed: {error_msg}")
            return redirect('cart')
    except requests.exceptions.Timeout:
        print("Cashfree API Timeout")
        messages.error(request, "Payment gateway timeout. Please try again.")
        return redirect('cart')
    except requests.exceptions.RequestException as e:
        print(f"Cashfree API Request Error: {str(e)}")
        messages.error(request, "Unable to connect to payment gateway. Please try again.")
        return redirect('cart')
    except Exception as e:
        print(f"Unexpected Error in initiate_payment: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('cart')

@csrf_exempt
@csrf_exempt
def payment_callback(request):
    """
    STRICT CALLBACK: Updates DB and triggers specific email workflow.
    Resilient to session loss by re-fetching user from Order.
    """
    order_id = (request.GET.get('order_id') or 
                request.GET.get('orderId') or 
                request.session.get('cashfree_order_id'))

    if not order_id:
        print("⚠️ Payment callback: No order_id found in request or session")
        # cleanup_payment_session(request) # Don't cleanup yet, might be able to recover
        return redirect('cart') # Can't do anything without order_id
    
    print(f"📋 Payment callback received for order: {order_id}")
    
    txn_id = order_id
    
    # [CRITICAL] RECOVER USER FROM ORDER
    # If session is lost, request.user is AnonymousUser.
    # We must fetch the original user from the Order record.
    try:
        # Get one order to find the user (all orders in batch have same user/txn_id)
        existing_order = Order.objects.filter(transaction_id=txn_id).first()
        if not existing_order:
            print(f"❌ Order not found for ID {txn_id}")
            messages.error(request, "Order not found.")
            return redirect('cart')
            
        auth_user = existing_order.user
        
        # If current session user is not the order user (e.g. logged out), 
        # use the auth_user for logic.
        user_to_use = auth_user
        
        # Optional: Log them back in if they are anonymous?
        # For now, we just ensure the backend logic uses `user_to_use`
        
    except Exception as e:
        print(f"Error recovering user from order: {e}")
        user_to_use = request.user

    if not user_to_use.is_authenticated:
        # Fallback if somehow order has no user (shouldn't happen)
        print("⚠️ User is not authenticated and could not be recovered.")
        return redirect('login')


    headers = {
        "Content-Type": "application/json",
        "x-api-version": settings.CASHFREE_API_VERSION,
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY
    }
    
    order_status = 'FAILED'
    
    try:
        print(f"🔍 Checking payment status with Cashfree API...")
        response = requests.get(f"{settings.CASHFREE_API_URL}/orders/{order_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            json_data = response.json()
            if json_data:
                order_status = json_data.get('order_status', 'FAILED')
                print(f"✅ Cashfree API Response: Status = {order_status}")
        else:
            print(f"⚠️ Cashfree API returned status code: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error checking payment status: {str(e)}")
        # Check DB status as fallback?
        pass

    if order_status == 'PAID':
        print(f"✅ Payment SUCCESSFUL for order {order_id}")
        
        # 1. Finalize the order in the database (Using RECOVERED USER)
        process_successful_order(user_to_use, txn_id)
        
        # 2. Email notifications (Async)
        successful_orders = Order.objects.filter(transaction_id=txn_id, payment_status='Success')
        from .notifications import send_all_order_notifications
        
        for order in successful_orders:
            try:
                send_all_order_notifications(order)
            except Exception as e:
                print(f"⚠️ Email notification error for order {order.order_id}: {str(e)}")
        
        print(f"✅ Payment successful! Order processed and emails triggered.")
        
        # 3. Cleanup Cart for this User
        # Logic: If this was a DIRECT order (DIR_), do NOT wipe the cart.
        # If this was a CART order (TXN_), wipe the cart.
        
        is_direct = str(txn_id).startswith("DIR")
        
        if not is_direct:
            # Cart Checkout -> Clear entire cart
            CartItem.objects.filter(user=user_to_use).delete()
            if 'cart' in request.session: request.session['cart'] = []
        
        # Always clear direct item from session if present
        if 'direct_item' in request.session: del request.session['direct_item']
        
        # Clean up payment session variables
        cleanup_payment_session(request)
        
        # Clear Coupon
        if 'applied_coupon_code' in request.session: 
            del request.session['applied_coupon_code']
        
        request.session.modified = True
        
        # If user is not logged in to session, maybe redirect to login with message?
        if not request.user.is_authenticated:
             # Logic to auto-login if backend allows, or just redirect to login
             from django.contrib.auth import login
             if hasattr(user_to_use, 'backend'):
                 login(request, user_to_use)
             else:
                 user_to_use.backend = 'django.contrib.auth.backends.ModelBackend'
                 login(request, user_to_use)

        messages.success(request, "Payment successful! Your order has been placed.")
        return redirect('profile')
    
    else:
        # Handle Failed/Cancelled Payment
        print(f"❌ Payment FAILED/CANCELLED for order {order_id}. Status: {order_status}")
        
        # Mark orders as failed in database (Using RECOVERED USER)
        handle_failed_order(user_to_use, txn_id)
        
        # Clean up payment session variables
        cleanup_payment_session(request)
        request.session.modified = True
        
         # If user is not logged in to session, login them back
        if not request.user.is_authenticated:
             from django.contrib.auth import login
             if hasattr(user_to_use, 'backend'):
                 login(request, user_to_use)
             else:
                 user_to_use.backend = 'django.contrib.auth.backends.ModelBackend'
                 login(request, user_to_use)

        # Provide user-friendly message
        if order_status == 'CANCELLED':
            messages.warning(request, "Payment was cancelled. Your items have been restored to your cart.")
        else:
            messages.warning(request, "Payment failed. Your items have been restored to your cart. Please try again.")
        
        print(f"✅ Items restored to cart. Redirecting to cart page.")
        return redirect('cart')



@login_required(login_url='login')
def cashfree_checkout(request):
    context = {'payment_session_id': request.session.get('cashfree_payment_session_id'), 'cashfree_env': 'production'}
    return render(request, 'core/cashfree_checkout.html', context)

# --- 🌐 5. STATIC PAGES ---
def home(request):
    # Fetch active popup offer
    now = timezone.now()
    active_offer = PopupOffer.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).order_by('-priority', '-created_at').first()
    
    return render(request, 'core/index.html', {
        'services': Service.objects.all()[:3],
        'popup_offer': active_offer
    })

def services_page(request):
    pricing = get_user_pricing(request.user) if request.user.is_authenticated else None
    config = PricingConfig.get_config()
    price_vars = {
        # Single-sided pricing
        'price_bw': float(config.admin_price_per_page),
        'price_bw_double': float(config.admin_price_per_page_double),
        # Color pricing - Show only the color price (as set in admin)
        'price_color': float(config.color_price_addition_admin),
        'price_color_double': float(config.color_price_addition_admin_double),
        # Color pricing - Addition only (for display)
        'color_addition_single': float(config.color_price_addition_admin),
        'color_addition_double': float(config.color_price_addition_admin_double),
        # Binding prices
        'spiral_binding': float(config.spiral_tier1_price_admin),
        'spiral_tier2': float(config.spiral_tier2_price_admin),
        'spiral_tier3': float(config.spiral_tier3_price_admin),
        'spiral_extra': float(config.spiral_extra_price_admin),
        'soft_binding': float(config.soft_binding_price_admin),
        # Custom layout prices
        'custom_1_4': float(config.custom_1_4_price_admin),
        'custom_1_8': float(config.custom_1_8_price_admin),
        'custom_1_9': float(config.custom_1_9_price_admin),
        'custom_1_8_double': float(config.custom_1_8_price_double_admin),
        'custom_1_9_double': float(config.custom_1_9_price_double_admin),
    }
    context = {
        'services': Service.objects.all(),
        'locations': Location.objects.all(),
        'pricing': pricing,
        'config': config,
        'price_vars': price_vars,
    }
    return render(request, 'core/services.html', context)

def about(request): return render(request, 'core/about.html')

def contact(request):
    if request.method == "POST":
        # Get form data
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        # Validate required fields
        if not all([name, phone, email, subject, message_text]):
            messages.error(request, "All fields are required.")
            return render(request, 'core/contact.html')
        
        # Prepare email content
        from django.core.mail import send_mail
        from django.conf import settings
        
        email_subject = f"Contact Form: {subject}"
        email_message = f"""
New contact form submission from FastCopy website:

Name: {name}
Phone: {phone}
Email: {email}
Subject: {subject}

Message:
{message_text}

---
This email was sent from the FastCopy contact form.
"""
        
        try:
            # Send email to admin
            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                ['fastcopyteam@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, "Thank you for contacting us! We'll get back to you soon.")
            return redirect('contact')
        except Exception as e:
            messages.error(request, "Failed to send message. Please try again later or contact us directly.")
            return render(request, 'core/contact.html')
    
    return render(request, 'core/contact.html')

def privacy_policy(request): return render(request, 'core/privacy_policy.html')
def terms_conditions(request): return render(request, 'core/terms_conditions.html')

# --- 🏪 6. DEALER DASHBOARD ---

def dealer_required(view_func):
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
            messages.error(request, "Access denied.")
            return redirect('dealer_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def dealer_login_view(request):
    if request.user.is_authenticated:
        try:
            if request.user.profile.is_dealer: return redirect('dealer_dashboard')
        except: pass
    if request.method == "POST":
        username, password = request.POST.get('username'), request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            try:
                if user.profile.is_dealer:
                    login(request, user)
                    return redirect('dealer_dashboard')
                else: messages.error(request, "Access denied.")
            except: messages.error(request, "Dealer profile not found.")
        else: messages.error(request, "Invalid credentials.")
    return render(request, 'dealer/dealer_login.html')
@dealer_required
def dealer_dashboard_view(request):
    pricing = get_user_pricing(request.user)
    
    def calculate_dealer_price(order):
        cost = 0.0
        pages, copies = order.pages, order.copies
        if order.service_name == "Custom Printing":
            layout = order.print_mode or ""
            divisor, rate = 4, pricing['custom_1_4_price']
            if "1/8" in layout: divisor, rate = 8, pricing['custom_1_8_price']
            elif "1/9" in layout: divisor, rate = 9, pricing['custom_1_9_price']
            sheets = -(-pages // divisor)
            cost = sheets * rate * copies
        else:
            is_double_sided = hasattr(order, 'side_type') and order.side_type == 'double'
            if 'custom' in str(order.print_mode).lower() and 'split' in str(order.print_mode).lower():
                from .utils import count_color_pages
                color_page_count = count_color_pages(order.custom_color_pages, pages)
                bw_page_count = pages - color_page_count
                color_rate = pricing['color_addition_double'] if is_double_sided else pricing['color_addition']
                bw_rate = pricing['price_per_page_double'] if is_double_sided else pricing['price_per_page']
                cost = ((color_page_count * color_rate) + (bw_page_count * bw_rate)) * copies
            elif order.print_mode == 'color':
                print_rate = pricing['color_addition_double'] if is_double_sided else pricing['color_addition']
                cost = pages * copies * print_rate
            else:
                print_rate = pricing['price_per_page_double'] if is_double_sided else pricing['price_per_page']
                cost = pages * copies * print_rate

        if "Spiral" in order.service_name:
            t1, t2, t3 = pricing['spiral_tier1_limit'], pricing['spiral_tier2_limit'], pricing['spiral_tier3_limit']
            if pages <= t1: binding = pricing['spiral_tier1_price']
            elif pages <= t2: binding = pricing['spiral_tier2_price']
            elif pages <= t3: binding = pricing['spiral_tier3_price']
            else: binding = pricing['spiral_tier3_price'] + ((-(-(pages-t3)//20)) * pricing['spiral_extra_price'])
            cost += (binding * copies)
        elif "Soft" in order.service_name:
            cost += (pricing['soft_binding'] * copies)
        return cost

    # --- 1. SET DEFAULTS & GET PARAMETERS ---
    date_filter = request.GET.get('date_filter')
    # If first load, default to 'today'
    if not date_filter:
        date_filter = 'today'
        
    status_filter = request.GET.get('status', 'all')
    service_filter = request.GET.get('service', 'all')
    
    # --- 2. BASE QUERYSET ---
    orders = Order.objects.filter(payment_status='Success')
    
    # Filter by dealer's assigned locations
    if hasattr(request.user, 'profile') and request.user.profile.dealer_locations.exists():
        loc_names = list(request.user.profile.dealer_locations.values_list('name', flat=True))
        orders = orders.filter(location__in=loc_names)
    else: 
        orders = orders.none()
    
    # --- 3. APPLY DATE FILTERING (STRICT RANGE LOGIC) ---
    now = timezone.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if date_filter == 'today': 
        # From 00:00:00 today until now
        orders = orders.filter(created_at__gte=start_of_today)
    elif date_filter == 'last_7_days': 
        # From 7 days ago 00:00:00 until now
        seven_days_ago = start_of_today - timedelta(days=7)
        orders = orders.filter(created_at__gte=seven_days_ago)
    elif date_filter == 'last_30_days': 
        # From 30 days ago 00:00:00 until now
        thirty_days_ago = start_of_today - timedelta(days=30)
        orders = orders.filter(created_at__gte=thirty_days_ago)
    # if 'all', no date filter applied
    
    # --- 4. APPLY STATUS & SERVICE FILTERS ---
    if status_filter != 'all': 
        orders = orders.filter(status=status_filter)
    # When 'all' is selected, show ALL orders (including Delivered, Rejected, etc.)
    # This allows dealers to see complete order history for amount calculation
    
    if service_filter != 'all': 
        orders = orders.filter(service_name__icontains=service_filter)
    
    # --- 5. CALCULATE METRICS & PREPARE DATA ---
    # Convert to list to iterate once and attach dealer_amount
    orders_list = list(orders.order_by('-created_at'))
    
    item_revenue = 0.0
    for o in orders_list:
        o.dealer_amount = calculate_dealer_price(o)
        item_revenue += float(o.dealer_amount)

    unique_txns_count = orders.values('transaction_id').distinct().count()
    delivery_revenue = unique_txns_count * float(pricing['delivery_charge'])
    
    context = {
        'total_orders': len(orders_list), 
        'total_revenue': item_revenue + delivery_revenue,
        'orders': orders_list, 
        'date_filter': date_filter,
        'status_filter': status_filter, 
        'service_filter': service_filter,
        'dealer_name': request.user.first_name or request.user.username,
    }
    return render(request, 'dealer/dealer_dashboard.html', context)
@dealer_required
def dealer_logout_view(request):
    logout(request); return redirect('dealer_login')

@dealer_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Ready', 'Delivered']:
            order.status = new_status
            order.save()
            messages.success(request, f"Order {order.order_id} updated.")
        else: messages.error(request, "Invalid status")
    return redirect('dealer_dashboard')

@dealer_required
def dealer_download_file(request, order_id):
    order = get_object_or_404(Order, id=order_id, payment_status='Success')
    if order.document and order.document.name:
        file_field = order.document
    elif order.image_upload and order.image_upload.name:
        file_field = order.image_upload
    else: raise Http404("No file found")
    
    try:
        file_path = file_field.path
        if not os.path.exists(file_path): raise Http404("File missing")
        _, ext = os.path.splitext(file_field.name)
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f"{order.order_id}{ext}")
        return response
    except Exception as e: raise Http404(f"Error: {str(e)}")


# ============================================================================
# 🤖 SEO: robots.txt View
# ============================================================================
def robots_txt(request):
    """
    Serve robots.txt file for search engine crawlers
    Includes sitemap reference and crawl rules
    """
    from django.conf import settings
    from django.http import HttpResponse
    
    # Get the site domain from settings
    site_url = settings.COMPANY_WEBSITE
    if not site_url.endswith('/'):
        site_url += '/'
    
    robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /cart/
Disallow: /checkout/
Disallow: /payment/
Disallow: /dealer/
Disallow: /profile/
Disallow: /login/
Disallow: /register/
Disallow: /logout/
Disallow: /media/uploads/

# Sitemap location
Sitemap: {site_url}sitemap.xml
"""
    
    return HttpResponse(robots_content, content_type="text/plain")

# --- 🛠️ 10. MAINTENANCE UTILITIES ---

def maintenance_view(request):
    """
    Renders the maintenance page.
    Only accessible if maintenance is active (or testing).
    Middleware normally handles the redirect logic.
    """
    try:
        settings_obj = MaintenanceSettings.get_settings()
        context = {
            'message': settings_obj.message,
            'duration': settings_obj.expected_duration,
            'updated_at': settings_obj.updated_at
        }
    except Exception as e:
        print(f"Maintenance View Error: {e}")
        context = {
            'message': 'We are upgrading our system. Back shortly!',
            'duration': 'Unknown'
        }
    return render(request, 'core/maintenance.html', context)