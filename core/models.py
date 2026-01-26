from django.db import models
from django.contrib.auth.models import User
import uuid

# --- 1. USER PROFILE MODEL ---

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class UserProfile(models.Model):
    """
    Extends the base Django User. 
    Stores: User ID, Name, Mobile, Email (via User), and Address.
    Format: FC_USER_0000000 (7 digits)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Custom Formatted ID Field
    fc_user_id = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False, 
        null=True, 
        blank=True
    )
    
    # Database storage for specific profile details
    mobile = models.CharField(max_length=15)
    address = models.TextField(null=True, blank=True)
    
    # Dealer-specific fields (Consolidated and Cleaned)
    is_dealer = models.BooleanField(default=False)
    is_delivery_boy = models.BooleanField(default=False, verbose_name="Is Delivery Partner")
    price_per_page = models.DecimalField(max_digits=5, decimal_places=2, default=1.50)
    dealer_locations = models.ManyToManyField(Location, blank=True, help_text="Select assigned locations for this dealer.")

    @property
    def name(self):
        """Returns the first_name from the Auth User table."""
        return self.user.first_name

    @property
    def email(self):
        """Returns the email from the Auth User table."""
        return self.user.email

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new and not self.fc_user_id:
            self.fc_user_id = f"FC_USER_{self.id:07d}"
            UserProfile.objects.filter(pk=self.pk).update(fc_user_id=self.fc_user_id)

    def __str__(self): 
        return f"{self.fc_user_id} | {self.user.username}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# --- 2. SERVICE MODEL ---
class Service(models.Model):
    """
    Stores types of services offered (Printing, Binding, etc.).
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self): 
        return self.name

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"


# --- 3. ORDER MODEL (MASTER ENGINE) ---
class Order(models.Model):
    """
    Handles confirmation and tracking of all orders.
    Format: FC_ORDER_0000000000 (10 digits)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=30, unique=True, editable=False, null=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    ORDER_SOURCE_CHOICES = [
        ('CART', 'Ordered from Cart Page'),
        ('SERVICE', 'Ordered from Service Page'),
    ]
    order_source = models.CharField(
        max_length=10, 
        choices=ORDER_SOURCE_CHOICES, 
        default='SERVICE'
    )

    service_name = models.CharField(max_length=100)
    print_mode = models.CharField(max_length=50) 
    side_type = models.CharField(max_length=20, default='single')
    copies = models.IntegerField(default=1)
    pages = models.IntegerField(default=1)
    custom_color_pages = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True, help_text="Contact number for this specific order")
    customer_name = models.CharField(max_length=150, null=True, blank=True, help_text="Name for this specific order")

    document = models.FileField(upload_to='orders/pdfs/', max_length=500, null=True, blank=True)
    image_upload = models.ImageField(upload_to='orders/images/', null=True, blank=True)

    # Pricing fields
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Coupon fields
    coupon_code = models.CharField(max_length=50, null=True, blank=True, help_text="Applied coupon code")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Discount amount from coupon")
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original price before discount")
    
    payment_status = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')],
        default='Pending'
    )
    status = models.CharField(
        max_length=20, 
        choices=[
            ('Pending', 'Pending'), 
            ('Confirmed', 'Confirmed'), 
            ('Ready', 'Ready'), 
            ('Delivered', 'Delivered'), 
            ('Rejected', 'Rejected'),
            ('Cancelled', 'Cancelled')
        ],
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        from .utils import calculate_delivery_date
        from django.utils import timezone
        
        is_new = self._state.adding
        if is_new and not self.order_id:
            self.order_id = f"TMP_{uuid.uuid4().hex[:10].upper()}"

        if self.print_mode == 'custom_split' and self.custom_color_pages:
            self.print_mode = f"Custom Split ({self.custom_color_pages})"

        if self.transaction_id:
            if self.transaction_id.startswith("DIR"):
                self.order_source = 'SERVICE'
            elif self.transaction_id.startswith("TXN"):
                self.order_source = 'CART'
        
        # Calculate estimated delivery date for new orders (if not already set)
        if is_new and not self.estimated_delivery_date:
            self.estimated_delivery_date = calculate_delivery_date(timezone.now())

        super().save(*args, **kwargs)

        if is_new and self.order_id.startswith('TMP_'):
            formatted_id = f"FC_ORDER_{self.id:010d}"
            Order.objects.filter(pk=self.pk).update(order_id=formatted_id)
            self.order_id = formatted_id

    def __str__(self): 
        return f"[{self.order_source}] {self.order_id}"

    class Meta:
        ordering = ['-created_at']


# --- 4. CART MODEL ---
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=255)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    document_name = models.CharField(max_length=255, null=True, blank=True)
    temp_path = models.CharField(max_length=500, null=True, blank=True)
    temp_image_path = models.CharField(max_length=500, null=True, blank=True)
    copies = models.IntegerField(default=1)
    pages = models.IntegerField(default=0)
    location = models.CharField(max_length=255, null=True, blank=True)
    print_mode = models.CharField(max_length=50, null=True, blank=True)
    side_type = models.CharField(max_length=50, default='single')
    custom_color_pages = models.TextField(null=True, blank=True, default="")
    mobile = models.CharField(max_length=15, null=True, blank=True)
    customer_name = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart: {self.service_name} | {self.user.username}"

    class Meta:
        ordering = ['-created_at']


# --- 5. PRICING CONFIGURATION MODEL ---
class PricingConfig(models.Model):
    """
    Centralized pricing configuration for all services.
    Supports separate pricing for admin users and dealers.
    """
    # Basic Printing Prices (per page) - Single Side
    admin_price_per_page = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.50,
        help_text="Price per page for regular users (admin rate) - Single Side"
    )
    dealer_price_per_page = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.20,
        help_text="Price per page for dealer users - Single Side"
    )
    
    # Basic Printing Prices (per page) - Double Side
    admin_price_per_page_double = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.50,
        help_text="Price per page for regular users (admin rate) - Double Side"
    )
    dealer_price_per_page_double = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00,
        help_text="Price per page for dealer users - Double Side"
    )
    
    # Spiral Binding Prices
    spiral_binding_price_admin = models.DecimalField(
        max_digits=6, decimal_places=2, default=20.00,
        help_text="Spiral binding price for regular users"
    )
    spiral_binding_price_dealer = models.DecimalField(
        max_digits=6, decimal_places=2, default=15.00,
        help_text="Spiral binding price for dealers"
    )
    
    # Soft Binding Prices
    soft_binding_price_admin = models.DecimalField(
        max_digits=6, decimal_places=2, default=30.00,
        help_text="Soft binding price for regular users"
    )
    soft_binding_price_dealer = models.DecimalField(
        max_digits=6, decimal_places=2, default=25.00,
        help_text="Soft binding price for dealers"
    )
    
    # Custom Print Layout Prices
    custom_1_4_price_admin = models.DecimalField(max_digits=5, decimal_places=2, default=2.00, verbose_name="1/4 Layout Price (Admin)")
    custom_1_4_price_dealer = models.DecimalField(max_digits=5, decimal_places=2, default=1.50, verbose_name="1/4 Layout Price (Dealer)")
    
    custom_1_8_price_admin = models.DecimalField(max_digits=5, decimal_places=2, default=4.00, verbose_name="1/8 Layout Price (Admin)")
    custom_1_8_price_dealer = models.DecimalField(max_digits=5, decimal_places=2, default=3.00, verbose_name="1/8 Layout Price (Dealer)")
    
    custom_1_9_price_admin = models.DecimalField(max_digits=5, decimal_places=2, default=4.00, verbose_name="1/9 Layout Price (Admin)")
    custom_1_9_price_dealer = models.DecimalField(max_digits=5, decimal_places=2, default=3.00, verbose_name="1/9 Layout Price (Dealer)")

    # Custom Layout Prices - Double Side
    custom_1_8_price_double_admin = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, verbose_name="1/8 Layout Price Double (Admin)")
    custom_1_8_price_double_dealer = models.DecimalField(max_digits=5, decimal_places=2, default=4.00, verbose_name="1/8 Layout Price Double (Dealer)")

    custom_1_9_price_double_admin = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, verbose_name="1/9 Layout Price Double (Admin)")
    custom_1_9_price_double_dealer = models.DecimalField(max_digits=5, decimal_places=2, default=4.00, verbose_name="1/9 Layout Price Double (Dealer)")

    # Spiral Binding Tiers
    spiral_tier1_limit = models.IntegerField(default=40)
    spiral_tier2_limit = models.IntegerField(default=60)
    spiral_tier3_limit = models.IntegerField(default=90)
    
    spiral_tier1_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=20.00)
    spiral_tier1_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=20.00)
    
    spiral_tier2_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=25.00)
    spiral_tier2_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=25.00)
    
    spiral_tier3_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=30.00)
    spiral_tier3_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=30.00)
    
    spiral_extra_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    spiral_extra_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    
    # Color Printing Additional Charge - Single Side
    color_price_addition_admin = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Additional charge per color page for regular users - Single Side"
    )
    color_price_addition_dealer = models.DecimalField(
        max_digits=5, decimal_places=2, default=3.00,
        help_text="Additional charge per color page for dealers - Single Side"
    )
    
    # Color Printing Additional Charge - Double Side
    color_price_addition_admin_double = models.DecimalField(
        max_digits=5, decimal_places=2, default=8.00,
        help_text="Additional charge per color page for regular users - Double Side"
    )
    color_price_addition_dealer_double = models.DecimalField(
        max_digits=5, decimal_places=2, default=6.00,
        help_text="Additional charge per color page for dealers - Double Side"
    )

    # Delivery Charge
    delivery_price_admin = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)
    delivery_price_dealer = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pricing Configuration"
        verbose_name_plural = "Pricing Configuration"
    
    def __str__(self):
        return f"Pricing Config (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

# --- 7. PUBLIC HOLIDAYS ---
class PublicHoliday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"


# --- 8. COUPON SYSTEM ---
class Coupon(models.Model):
    """
    Coupon model for discount management.
    Supports percentage-based discounts with various validation rules.
    """
    code = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Unique coupon code (e.g., SAVE20, WELCOME10)"
    )
    
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Discount percentage (e.g., 10.00 for 10% off)"
    )
    
    valid_from = models.DateTimeField(
        help_text="Coupon becomes active from this date/time"
    )
    
    valid_until = models.DateTimeField(
        help_text="Coupon expires after this date/time"
    )
    
    minimum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        help_text="Minimum order amount required to use this coupon"
    )
    
    max_usage_count = models.IntegerField(
        default=0,
        help_text="Maximum number of times this coupon can be used (0 = unlimited)"
    )
    
    current_usage_count = models.IntegerField(
        default=0,
        editable=False,
        help_text="Current number of times this coupon has been used"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this coupon"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Internal description or notes about this coupon"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
    
    def __str__(self):
        return f"{self.code} ({self.discount_percentage}% off)"
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False, "This coupon is not active"
        
        if now < self.valid_from:
            return False, "This coupon is not yet valid"
        
        if now > self.valid_until:
            return False, "This coupon has expired"
        
        if self.max_usage_count > 0 and self.current_usage_count >= self.max_usage_count:
            return False, "This coupon has reached its usage limit"
        
        return True, "Coupon is valid"
    
    def can_apply_to_order(self, order_total):
        """Check if coupon can be applied to an order with given total"""
        is_valid, message = self.is_valid()
        
        if not is_valid:
            return False, message
        
        if order_total < self.minimum_order_amount:
            return False, f"Minimum order amount of ₹{self.minimum_order_amount} required"
        
        return True, "Coupon can be applied"
    
    def calculate_discount(self, order_total):
        """Calculate discount amount for given order total"""
        can_apply, message = self.can_apply_to_order(order_total)
        
        if not can_apply:
            return 0.00, message
        
        # Convert Decimal to float to avoid type mismatch
        discount_amount = (float(order_total) * float(self.discount_percentage)) / 100
        return float(discount_amount), f"{self.discount_percentage}% discount applied"
    
    def increment_usage(self):
        """Increment usage count when coupon is used"""
        self.current_usage_count += 1
        self.save()


# --- 10. POPUP OFFER MODEL ---
class PopupOffer(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='offers/', help_text="Upload an image for the popup/modal")
    action_url = models.URLField(blank=True, null=True, help_text="Optional URL to redirect when clicked")
    
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(help_text="When to start showing this offer")
    end_date = models.DateTimeField(help_text="When to stop showing this offer")
    priority = models.IntegerField(default=1, help_text="Higher number means higher priority if multiple overlap")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        
    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"
# --- 7. MAINTENANCE MODE SETTINGS ---

class MaintenanceSettings(models.Model):
    """
    Singleton model to manage Maintenance Mode settings.
    Only one instance should exist.
    """
    is_enabled = models.BooleanField(default=False, verbose_name="Maintenance Mode Enabled")
    message = models.TextField(
        default="We are upgrading our system to serve you better. We will be back shortly!",
        help_text="Message to display to users on the maintenance page."
    )
    expected_duration = models.CharField(
        max_length=100, 
        default="2 hours", 
        help_text="Expected duration text (e.g., '2 hours', '30 minutes')"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Maintenance Settings"
        verbose_name_plural = "Maintenance Settings"

    def __str__(self):
        status = "ON" if self.is_enabled else "OFF"
        return f"Maintenance Mode: {status}"

    def save(self, *args, **kwargs):
        # Singleton logic: Ensure only one instance exists
        if not self.pk and MaintenanceSettings.objects.exists():
            return MaintenanceSettings.objects.first()
        return super(MaintenanceSettings, self).save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj
