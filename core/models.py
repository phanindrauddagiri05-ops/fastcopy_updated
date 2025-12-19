from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    def __str__(self): return self.user.username

from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50)
    theme_color = models.CharField(max_length=20, default="#2563eb")
    def __str__(self): return self.name

class Order(models.Model):
    STATUS_CHOICES = [('In Progress', 'In Progress'), ('Ready', 'Ready'), ('Delivered', 'Delivered')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    service_name = models.CharField(max_length=100)
    document = models.FileField(upload_to='orders/', null=True, blank=True)
    print_type = models.CharField(max_length=20, default='bw')
    side_type = models.CharField(max_length=20, default='1')
    copies = models.IntegerField(default=1)
    total_price = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)