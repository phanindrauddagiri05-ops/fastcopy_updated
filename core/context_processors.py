from .models import CartItem

def cart_count(request):
    """
    Returns the total number of items in the user's cart for global template access.
    Usage in templates: {{ cart_item_count }}
    """
    if request.user.is_authenticated:
        # Count actual rows in the DB for the logged-in user
        count = CartItem.objects.filter(user=request.user).count()
    else:
        # Fallback to session count for guest users (if any)
        cart = request.session.get('cart', [])
        count = len(cart)
        
    return {
        'cart_item_count': count
    }
<<<<<<< HEAD

from django.utils import timezone
from .models import PublicHoliday
from .utils import calculate_delivery_date

def site_context(request):
    """
    Global context for templates. 
    Provides upcoming public holidays and dynamic delivery dates for marquee.
    """
    now = timezone.localtime(timezone.now())
    today = now.date()
    
    # Calculate delivery dates for Marquee display
    # Scenario 1: Order placed Right Now (or theoretical < 8 PM today)
    # Actually, the marquee text says "Order Before 8 PM: Delivery Next Working Day".
    # So we should show the date for a theoretical order placed BEFORE 8 PM Today.
    # Logic: If current time > 8 PM, "Before 8 PM" refers to *Tomorrow*? No, usually refers to Today.
    # But if it's 9 PM Today, "Order Before 8 PM" is impossible for Today. 
    # However, keeping it simple: Use "Today 12:00 PM" to simulate < 8 PM scenario.
    
    simulated_early = now.replace(hour=12, minute=0, second=0)
    simulated_late = now.replace(hour=21, minute=0, second=0)
    
    date_before_8pm = calculate_delivery_date(simulated_early)
    date_after_8pm = calculate_delivery_date(simulated_late)

    # Fetch next 3 upcoming holidays
    upcoming_holidays = PublicHoliday.objects.filter(date__gte=today).order_by('date')[:3]
    
    return {
        'upcoming_holidays': upcoming_holidays,
        'marquee_date_early': date_before_8pm,
        'marquee_date_late': date_after_8pm,
    }
=======
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
