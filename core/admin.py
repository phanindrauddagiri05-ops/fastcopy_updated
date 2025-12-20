from django.contrib import admin
from .models import Service, Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'service_name', 'total_price', 'status', 'created_at')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name',)