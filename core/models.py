from django.db import models
from django.contrib.auth.models import User
import uuid

class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=100)
    total_price = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} - {self.user.username}"

class Service(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50) 
    description = models.TextField()
    theme_color = models.CharField(max_length=20, default="#2563eb")

    def __str__(self):
        return self.name