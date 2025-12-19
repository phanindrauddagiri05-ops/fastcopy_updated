from django.contrib import admin
from .models import Service, Profile, Order

# Inline display to see Profile info within the User admin
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

# Extend the default User Admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # What columns show up in the admin list
    list_display = ('id', 'get_user_name', 'get_mobile', 'service_name', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__first_name', 'user__username')
    list_editable = ('status',) # Allows you to change status directly from the list!

    def get_user_name(self, obj):
        return obj.user.first_name
    get_user_name.short_description = 'Customer Name'

    def get_mobile(self, obj):
        return obj.user.profile.mobile
    get_mobile.short_description = 'Mobile'