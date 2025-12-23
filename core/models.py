from django.db import models
from django.contrib.auth.models import User

# --- 1. USER PROFILE MODEL ---
class UserProfile(models.Model):
    """
    Extends the base Django User. 
    Stores custom User ID in format: FC_USER_0000
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Custom Formatted ID Field - This is the field that was missing in your DB
    fc_user_id = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False, 
        null=True, 
        blank=True
    )
    
    mobile = models.CharField(max_length=15)
    address = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate FC_USER_0000 format based on primary key
        if not self.fc_user_id:
            # Save first to get an auto-increment ID if it's a new record
            super().save(*args, **kwargs)
            self.fc_user_id = f"FC_USER_{self.id:04d}"
            # Remove force_insert to allow the second save to update the record
            kwargs.pop('force_insert', None)
        
        super().save(*args, **kwargs)

    def __str__(self): 
        return f"{self.fc_user_id} | {self.user.username}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# --- 2. SERVICE MODEL ---
class Service(models.Model):
    """
    Stores types of services offered.
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
    Order ID format: FC_ORDER_0000000000
    Stores transaction details and printing configurations.
    """
    # Formatted Order ID
    order_id = models.CharField(max_length=30, unique=True, editable=False, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    service_name = models.CharField(max_length=100)
    document = models.FileField(upload_to='orders/', null=True, blank=True)
    
    # Printing Mode Logic (bw, color, or custom(pages))
    print_mode = models.CharField(max_length=100, default='bw')
    custom_color_pages = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        help_text="Stores raw page numbers before formatting"
    )
    
    side_type = models.CharField(max_length=50, default='single')
    copies = models.IntegerField(default=1)
    location = models.CharField(max_length=100, null=True, blank=True)
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Ready', 'Ready'),
        ('Delivered', 'Delivered'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # India Localized Time
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Generate FC_ORDER_0000000000 format
        if not self.order_id:
            super().save(*args, **kwargs)
            self.order_id = f"FC_ORDER_{self.id:010d}"
            kwargs.pop('force_insert', None)

        # 2. Logic for Custom print_mode format
        if self.print_mode == 'custom_split' and self.custom_color_pages:
            self.print_mode = f"custom({self.custom_color_pages})"
        elif self.print_mode and "(" not in self.print_mode:
            self.print_mode = self.print_mode.lower()

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.order_id)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']