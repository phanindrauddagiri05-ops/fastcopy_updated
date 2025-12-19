from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50)
    short_description = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, unique=True)
    address = models.TextField()

    def __str__(self):
        return f"{self.user.first_name}'s Profile"
    


class Order(models.Model):
    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Ready', 'Order is Ready'),
        ('Delivered', 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    service_name = models.CharField(max_length=100)
    document = models.FileField(upload_to='orders/')
    print_type = models.CharField(max_length=20) # B&W or Color
    side_type = models.CharField(max_length=20)
    copies = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.first_name}"