
import os

def fix_views():
    file_path = 'core/views.py'
    snippet_path = 'core/views_delivery_snippet.py'
    
    print(f"Reading {file_path} in binary mode...")
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # locate the last valid line of the original file
    # "return render(request, 'core/maintenance.html', context)"
    marker = b"return render(request, 'core/maintenance.html', context)"
    
    idx = content.find(marker)
    if idx == -1:
        print("❌ Could not find the marker in views.py! Aborting to avoid data loss.")
        return

    # Calculate end of that line
    # We want to keep the marker and the newline/whitespace immediately following it, potentially.
    # But strictly, we can just cut off after the marker and a few bytes (like `\n` or `\r\n`)
    
    # Let's find the newline after the marker
    end_idx = content.find(b'\n', idx)
    if end_idx == -1:
        end_idx = idx + len(marker)
    else:
        end_idx += 1 # Include the \n
        
    print(f"Truncating file at byte {end_idx}...")
    clean_content = content[:end_idx]
    
    # Read the snippet
    print(f"Reading snippet {snippet_path}...")
    if os.path.exists(snippet_path):
        with open(snippet_path, 'rb') as f:
            snippet_content = f.read()
    else:
        # Fallback if snippet file not found (we know what it is)
        print("Snippet file not found, using embedded content.")
        snippet_content = b"""
# --- DELIVERY BOY VIEWS ---

def delivery_required(view_func):
    \"\"\"Decorator to restrict access to delivery boys only.\"\"\"
    from django.shortcuts import redirect
    from django.contrib import messages
    
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('delivery_login')
        try:
            if not request.user.profile.is_delivery_boy:
                messages.error(request, "Access denied. Delivery personnel only.")
                return redirect('delivery_login')
        except:
            return redirect('delivery_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def delivery_login_view(request):
    from django.contrib.auth import authenticate, login
    from django.shortcuts import render, redirect
    from django.contrib import messages

    if request.user.is_authenticated:
        try:
            if request.user.profile.is_delivery_boy: return redirect('delivery_dashboard')
        except: pass
    if request.method == "POST":
        username, password = request.POST.get('username'), request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            try:
                if user.profile.is_delivery_boy:
                    login(request, user)
                    return redirect('delivery_dashboard')
                else: messages.error(request, "Access denied. Delivery personnel only.")
            except: messages.error(request, "Delivery profile not found.")
        else: messages.error(request, "Invalid credentials.")
    return render(request, 'delivery/login.html')

@delivery_required
def delivery_dashboard_view(request):
    from .models import Order
    from django.utils import timezone
    from django.shortcuts import render

    status_filter = request.GET.get('status', 'all')
    orders = Order.objects.filter(payment_status='Success')
    
    if hasattr(request.user, 'profile') and request.user.profile.dealer_locations.exists():
        loc_names = list(request.user.profile.dealer_locations.values_list('name', flat=True))
        orders = orders.filter(location__in=loc_names)
    
    if status_filter != 'all': 
        orders = orders.filter(status=status_filter)
    
    orders = orders.order_by('-created_at')
    
    context = {
        'total_orders': orders.count(), 
        'orders': orders, 
        'status_filter': status_filter, 
        'delivery_name': request.user.first_name or request.user.username,
    }
    return render(request, 'delivery/dashboard.html', context)

@delivery_required
def delivery_logout_view(request):
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    logout(request); return redirect('delivery_login')

@delivery_required
def update_delivery_status(request, order_id):
    from .models import Order
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.order_id} status updated to {new_status}")
        return redirect('delivery_dashboard')
    return redirect('delivery_dashboard')
"""

    
    # Combine
    new_content = clean_content + b"\n\n" + snippet_content
    
    print("Writing fixed content back to core/views.py...")
    with open(file_path, 'wb') as f:
        f.write(new_content)
    
    print("✅ Successfully fixed views.py encoding!")

if __name__ == "__main__":
    fix_views()
