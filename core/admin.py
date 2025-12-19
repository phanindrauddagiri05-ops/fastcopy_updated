from django.contrib import admin
from .models import Service, Profile, Order

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # list_display[4] is 'status' - matches model now
    list_display = ('id', 'user', 'service_name', 'total_price', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'created_at')

admin.site.register(Profile)