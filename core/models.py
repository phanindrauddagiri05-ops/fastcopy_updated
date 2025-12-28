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
<<<<<<< HEAD
    
    # Dealer-specific fields
    is_dealer = models.BooleanField(default=False)
    price_per_page = models.DecimalField(max_digits=5, decimal_places=2, default=1.50)
    dealer_locations = models.ManyToManyField(Location, blank=True, help_text="Select assigned locations for this dealer.")
=======
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc

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

    document = models.FileField(upload_to='orders/pdfs/', null=True, blank=True)
    image_upload = models.ImageField(upload_to='orders/images/', null=True, blank=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
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
    estimated_delivery_date = models.DateField(null=True, blank=True) # New Delivery Field



    def save(self, *args, **kwargs):
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
    Only one instance should exist (singleton pattern).
    """
    # Basic Printing Prices (per page)
    admin_price_per_page = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.50,
        help_text="Price per page for regular users (admin rate)"
    )
    dealer_price_per_page = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.20,
        help_text="Price per page for dealer users"
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

    # Spiral Binding Tiers (Limits)
    spiral_tier1_limit = models.IntegerField(default=40, help_text="Page limit for Tier 1")
    spiral_tier2_limit = models.IntegerField(default=60, help_text="Page limit for Tier 2")
    spiral_tier3_limit = models.IntegerField(default=90, help_text="Page limit for Tier 3")
    
    # Spiral Binding Tier Prices
    spiral_tier1_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=20.00, verbose_name="Spiral Tier 1 Price (Admin)")
    spiral_tier1_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=20.00, verbose_name="Spiral Tier 1 Price (Dealer)")
    
    spiral_tier2_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=25.00, verbose_name="Spiral Tier 2 Price (Admin)")
    spiral_tier2_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=25.00, verbose_name="Spiral Tier 2 Price (Dealer)")
    
    spiral_tier3_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=30.00, verbose_name="Spiral Tier 3 Price (Admin)")
    spiral_tier3_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=30.00, verbose_name="Spiral Tier 3 Price (Dealer)")
    
    spiral_extra_price_admin = models.DecimalField(max_digits=6, decimal_places=2, default=5.00, help_text="Extra cost per 20 pages above Tier 3 (Admin)")
    spiral_extra_price_dealer = models.DecimalField(max_digits=6, decimal_places=2, default=5.00, help_text="Extra cost per 20 pages above Tier 3 (Dealer)")
    
    # Color Printing Additional Charge (per color page)
    color_price_addition_admin = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Additional charge per color page for regular users"
    )
    color_price_addition_dealer = models.DecimalField(
        max_digits=5, decimal_places=2, default=3.00,
        help_text="Additional charge per color page for dealers"
    )

    # Delivery Charge (Per Order)
    delivery_price_admin = models.DecimalField(max_digits=5, decimal_places=2, default=40.00, verbose_name="Delivery Charge (Admin)")
    delivery_price_dealer = models.DecimalField(max_digits=5, decimal_places=2, default=30.00, verbose_name="Delivery Charge (Dealer)")
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pricing Configuration"
        verbose_name_plural = "Pricing Configuration"
    
    def __str__(self):
        return f"Pricing Config (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def get_config(cls):
        """Get or create the single pricing configuration instance"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def save(self, *args, **kwargs):
        """Ensure only one PricingConfig instance exists"""
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