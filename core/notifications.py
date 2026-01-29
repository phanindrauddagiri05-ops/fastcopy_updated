"""
Email notification utilities for FastCopy
Handles sending order confirmation and alert emails to customers, admins, and dealers
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from core.models import UserProfile
import logging

logger = logging.getLogger(__name__)


def calculate_dealer_price_for_order(order):
    """
    Calculate dealer price for an order (what dealer earns)
    Uses dealer pricing rates instead of admin rates
    """
    from core.models import PricingConfig
    
    config = PricingConfig.get_config()
    
    # Use dealer pricing
    pricing = {
        'price_per_page': float(config.dealer_price_per_page),
        'price_per_page_double': float(config.dealer_price_per_page_double),
        'color_addition': float(config.color_price_addition_dealer),
        'color_addition_double': float(config.color_price_addition_dealer_double),
        'custom_1_4_price': float(config.custom_1_4_price_dealer),
        'custom_1_8_price': float(config.custom_1_8_price_dealer),
        'custom_1_9_price': float(config.custom_1_9_price_dealer),
        'spiral_tier1_limit': config.spiral_tier1_limit,
        'spiral_tier2_limit': config.spiral_tier2_limit,
        'spiral_tier3_limit': config.spiral_tier3_limit,
        'spiral_tier1_price': float(config.spiral_tier1_price_dealer),
        'spiral_tier2_price': float(config.spiral_tier2_price_dealer),
        'spiral_tier3_price': float(config.spiral_tier3_price_dealer),
        'spiral_extra_price': float(config.spiral_extra_price_dealer),
        'soft_binding': float(config.soft_binding_price_dealer),
    }
    
    cost = 0.0
    pages, copies = order.pages, order.copies
    
    if order.service_name == "Custom Printing":
        layout = order.print_mode or ""
        divisor, rate = 4, pricing['custom_1_4_price']
        if "1/8" in layout:
            divisor, rate = 8, pricing['custom_1_8_price']
        elif "1/9" in layout:
            divisor, rate = 9, pricing['custom_1_9_price']
        sheets = -(-pages // divisor)
        cost = sheets * rate * copies
    else:
        # Determine if it's single or double-sided
        is_double_sided = hasattr(order, 'side_type') and order.side_type == 'double'
        
        # Check for custom split mode (some pages color, some B&W)
        if 'custom' in str(order.print_mode).lower() and 'split' in str(order.print_mode).lower():
            from .utils import count_color_pages
            
            # Count how many pages are color vs B&W
            color_page_count = count_color_pages(order.custom_color_pages, pages)
            bw_page_count = pages - color_page_count
            
            # Get rates for both types
            color_rate = pricing['color_addition_double'] if is_double_sided else pricing['color_addition']
            bw_rate = pricing['price_per_page_double'] if is_double_sided else pricing['price_per_page']
            
            # Calculate split cost: (color pages × color rate) + (B&W pages × B&W rate)
            cost = ((color_page_count * color_rate) + (bw_page_count * bw_rate)) * copies
        elif order.print_mode == 'color':
            # All pages are color
            # Use ONLY color price from configuration (not B&W + color)
            print_rate = pricing['color_addition_double'] if is_double_sided else pricing['color_addition']
            cost = pages * copies * print_rate
        else:
            # All pages are B&W
            # Use B&W price for black and white prints
            print_rate = pricing['price_per_page_double'] if is_double_sided else pricing['price_per_page']
            cost = pages * copies * print_rate

    
    # Add binding costs
    if "Spiral" in order.service_name:
        t1, t2, t3 = pricing['spiral_tier1_limit'], pricing['spiral_tier2_limit'], pricing['spiral_tier3_limit']
        if pages <= t1:
            binding = pricing['spiral_tier1_price']
        elif pages <= t2:
            binding = pricing['spiral_tier2_price']
        elif pages <= t3:
            binding = pricing['spiral_tier3_price']
        else:
            binding = pricing['spiral_tier3_price'] + ((-(-(pages-t3)//20)) * pricing['spiral_extra_price'])
        cost += (binding * copies)
    elif "Soft" in order.service_name:
        cost += (pricing['soft_binding'] * copies)
    
    return round(cost, 2)



def send_customer_order_confirmation(order):
    """
    Send order confirmation email to customer
    Args:
        order: Order object
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        customer = order.user
        customer_name = customer.first_name or customer.username
        
        print(f"DEBUG: Attempting to send customer email for order {order.order_id}")
        print(f"DEBUG: Customer email: {customer.email}")
        
        if not customer.email or customer.email == '':
            logger.warning(f"Customer {customer.username} has no email address. Skipping confirmation email.")
            print(f"WARNING: Customer {customer.username} has no email address!")
            return False
        
        context = {
            'order': order,
            'customer_name': customer_name,
            'support_email': settings.SUPPORT_EMAIL,
            'support_phone': settings.SUPPORT_PHONE,
            'company_name': settings.COMPANY_NAME,
        }
        
        # Render HTML email
        html_content = render_to_string('emails/order_confirmation.html', context)
        text_content = strip_tags(html_content)
        
        subject = f'Order Confirmation - {order.order_id} | {settings.COMPANY_NAME}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [customer.email]
        
        print(f"DEBUG: Sending email to {recipient_list} from {from_email}")
        
        # Create email with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Order confirmation email sent to {customer.email} for order {order.order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send customer confirmation email for order {order.order_id}: {str(e)}")
        return False


def send_admin_order_alert(order):
    """
    Send new order alert email to admin
    Args:
        order: Order object
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        customer = order.user
        customer_profile = UserProfile.objects.filter(user=customer).first()
        
        customer_name = customer.first_name or customer.username
        customer_phone = customer_profile.mobile if customer_profile else 'N/A'
        
        context = {
            'order': order,
            'customer_name': customer_name,
            'customer_email': customer.email,
            'customer_phone': customer_phone,
            'company_name': settings.COMPANY_NAME,
            'admin_panel_url': f"{settings.COMPANY_WEBSITE}/admin/core/order/{order.id}/change/",
        }
        
        # Render HTML email
        html_content = render_to_string('emails/admin_new_order.html', context)
        text_content = strip_tags(html_content)
        
        subject = f'🔔 New Order Alert - {order.order_id} | ₹{order.total_price}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.ADMIN_EMAIL]
        
        # Create email with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Admin alert email sent to {settings.ADMIN_EMAIL} for order {order.order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin alert email for order {order.order_id}: {str(e)}")
        return False


def send_dealer_order_alert(order):
    """
    Send new order alert to dealers assigned to the order location
    Args:
        order: Order object
    Returns:
        int: Number of emails sent successfully
    """
    print(f"DEBUG: Checking dealer notifications for order {order.order_id}")
    print(f"DEBUG: Order location: {order.location}")
    
    if not order.location:
        logger.info(f"Order {order.order_id} has no location, skipping dealer notifications")
        print(f"WARNING: Order {order.order_id} has no location!")
        return 0
    
    try:
        from core.models import Location
        
        # Find the location object
        location = Location.objects.filter(name=order.location).first()
        print(f"DEBUG: Looking for location '{order.location}' in database...")
        
        if not location:
            logger.warning(f"Location '{order.location}' not found in database for order {order.order_id}")
            print(f"WARNING: Location '{order.location}' NOT FOUND in database!")
            return 0
        
        print(f"DEBUG: Location found: {location}")
        
        # Find all dealers assigned to this location
        dealers = UserProfile.objects.filter(
            is_dealer=True,
            dealer_locations=location
        ).select_related('user')
        
        dealer_count = dealers.count()
        print(f"DEBUG: Found {dealer_count} dealer(s) assigned to location '{order.location}'")
        
        if not dealers.exists():
            logger.info(f"No dealers assigned to location '{order.location}' for order {order.order_id}")
            print(f"INFO: No dealers assigned to location '{order.location}'")
            return 0
        
        customer = order.user
        customer_profile = UserProfile.objects.filter(user=customer).first()
        customer_name = customer.first_name or customer.username
        customer_phone = customer_profile.mobile if customer_profile else 'N/A'
        
        emails_sent = 0
        
        for dealer_profile in dealers:
            try:
                dealer_name = dealer_profile.user.first_name or dealer_profile.user.username
                dealer_email = dealer_profile.user.email
                
                print(f"DEBUG: Sending dealer email to {dealer_name} <{dealer_email}>")
                
                if not dealer_email or dealer_email == '':
                    print(f"WARNING: Dealer {dealer_name} has no email address! Skipping.")
                    continue
                
                # Calculate dealer amount (what dealer earns)
                dealer_amount = calculate_dealer_price_for_order(order)
                print(f"DEBUG: Dealer amount calculated: ₹{dealer_amount} (Customer paid: ₹{order.total_price})")
                
                context = {
                    'order': order,
                    'dealer_name': dealer_name,
                    'customer_name': customer_name,
                    'customer_phone': customer_phone,
                    'dealer_amount': dealer_amount,  # Dealer's earning
                    'company_name': settings.COMPANY_NAME,
                    'support_email': settings.SUPPORT_EMAIL,
                }
                
                # Render HTML email
                html_content = render_to_string('emails/dealer_new_order.html', context)
                text_content = strip_tags(html_content)
                
                subject = f'📦 New Order in {order.location} - {order.order_id}'
                from_email = settings.DEFAULT_FROM_EMAIL
                
                # Create and send email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[dealer_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                logger.info(f"Dealer alert sent to {dealer_email} for order {order.order_id}")
                print(f"SUCCESS: Dealer email sent to {dealer_email}")
                emails_sent += 1
                
            except Exception as e:
                logger.error(f"Failed to send dealer alert to {dealer_profile.user.email}: {str(e)}")
                print(f"ERROR: Failed to send dealer email to {dealer_profile.user.email}: {str(e)}")
                continue
        
        print(f"DEBUG: Sent {emails_sent} dealer email(s) successfully")
        return emails_sent
        
    except Exception as e:
        logger.error(f"Failed to send dealer alerts for order {order.order_id}: {str(e)}")
        print(f"ERROR: Dealer notification system error: {str(e)}")
        return 0


def send_all_order_notifications(order):
    """
    Send all order notifications (customer, admin, and dealers)
    Args:
        order: Order object
    Returns:
        dict: Status of each notification type
    """
    print(f"\n========== EMAIL NOTIFICATIONS FOR ORDER {order.order_id} ==========")
    print(f"Order ID: {order.order_id}")
    print(f"Customer: {order.user.username} ({order.user.email})")
    print(f"Location: {order.location}")
    print("=" * 70)
    
    results = {
        'customer_email': False,
        'admin_email': False,
        'dealer_emails_count': 0,
    }
    
    # Send customer confirmation
    print("\n--- Sending Customer Confirmation Email ---")
    results['customer_email'] = send_customer_order_confirmation(order)
    print(f"Customer email result: {results['customer_email']}")
    
    # Send admin alert
    # print("\n--- Sending Admin Alert Email ---")
    # results['admin_email'] = send_admin_order_alert(order)
    # print(f"Admin email result: {results['admin_email']}")
    results['admin_email'] = False # Disabled as per requirements
    
    # Send dealer alerts
    print("\n--- Sending Dealer Alert Emails ---")
    results['dealer_emails_count'] = send_dealer_order_alert(order)
    print(f"Dealer emails sent: {results['dealer_emails_count']}")
    
    logger.info(f"Notification summary for order {order.order_id}: {results}")
    print(f"\n========== EMAIL NOTIFICATIONS COMPLETE ==========\n")
    
    return results
