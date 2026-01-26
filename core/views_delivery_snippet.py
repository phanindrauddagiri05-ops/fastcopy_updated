
# --- DELIVERY BOY VIEWS ---

def delivery_required(view_func):
    """Decorator to restrict access to delivery boys only."""
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
    # --- 1. SET DEFAULTS & GET PARAMETERS ---
    status_filter = request.GET.get('status', 'all')
    
    # --- 2. BASE QUERYSET ---
    # Delivery boys see orders that are Ready or Out for Delivery initially, or ALL if requested
    orders = Order.objects.filter(payment_status='Success')
    
    # Filter by dealer's assigned locations
    # (Delivery boys likely serve specific locations too, reusing dealer_locations field logic for now or showing all if generic)
    if hasattr(request.user, 'profile') and request.user.profile.dealer_locations.exists():
        loc_names = list(request.user.profile.dealer_locations.values_list('name', flat=True))
        orders = orders.filter(location__in=loc_names)
    
    # --- 3. APPLY STATUS FILTER ---
    if status_filter != 'all': 
        orders = orders.filter(status=status_filter)
    else:
        # Default view for delivery: Show active delivery tasks
        # orders = orders.filter(status__in=['Ready', 'Out for Delivery'])
        pass # Showing all as per user request to be like dealer dashboard
    
    orders_list = orders.order_by('-created_at')
    
    context = {
        'total_orders': orders_list.count(), 
        'orders': orders_list, 
        'status_filter': status_filter, 
        'delivery_name': request.user.first_name or request.user.username,
    }
    return render(request, 'delivery/dashboard.html', context)

@delivery_required
def delivery_logout_view(request):
    logout(request); return redirect('delivery_login')

@delivery_required
def update_delivery_status(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.order_id} status updated to {new_status}")
        return redirect('delivery_dashboard')
    return redirect('delivery_dashboard')
