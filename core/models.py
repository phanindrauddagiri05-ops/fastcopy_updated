from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, unique=True)
    address = models.TextField()

class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=100)
    file_name = models.CharField(max_length=255, default="No file") # THE FIX
    total_price = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional fields for detail view
    print_type = models.CharField(max_length=50, blank=True, null=True)
    side_type = models.CharField(max_length=50, blank=True, null=True)
    copies = models.IntegerField(default=1)
    
class Service(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50) # FontAwesome icons
    description = models.TextField()
    theme_color = models.CharField(max_length=20, default="#2563eb")

    def __str__(self):
        return self.name
