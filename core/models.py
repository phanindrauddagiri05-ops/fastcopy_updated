from django.db import models
from django.contrib.auth.models import User
import uuid

# --- 1. USER PROFILE MODEL ---
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

    # Note: Name and Email are handled by the built-in Django User model
    # linked via the OneToOneField. We use properties for easy access.

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
        # Step 1: Initial save to get the primary key (id)
        super().save(*args, **kwargs)
        
        # Step 2: Generate FC_USER_0000000 format after ID is available
        if is_new and not self.fc_user_id:
            self.fc_user_id = f"FC_USER_{self.id:07d}"
            # Use update to bypass re-triggering save() and recursion
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