from django.contrib import admin
from .models import Service, Order, UserProfile

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'service_name', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'service_name', 'order_id')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile', 'address')

admin.site.register(Order, OrderAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Service)