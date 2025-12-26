from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import Service, Order, UserProfile, CartItem

# --- 🛠️ 1. CUSTOM ADMIN SITE SETUP ---
class FastCopyAdminSite(admin.AdminSite):
    site_header = "FastCopy Admin"
    site_title = "FastCopy Portal"
    index_title = "Operations Hub"

admin_site = FastCopyAdminSite(name='fastcopy_admin')

# --- 🔍 2. CUSTOM SERVICE FILTER ---
class ServiceTypeFilter(admin.SimpleListFilter):
    title = 'By service name'
    parameter_name = 'service_name'

    def lookups(self, request, model_admin):
        return (
            ('Printing', 'Printing'),
            ('Soft Binding', 'Soft Binding'),
            ('Spiral Binding', 'Spiral Binding'),
            ('Custom Printing', 'Custom Printing'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(service_name=self.value())
        return queryset

# --- 🛒 3. CART ITEM ADMIN ---
@admin.register(CartItem, site=admin_site)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_name', 'total_price', 'pages', 'copies', 'created_at')
    list_filter = ('service_name', 'created_at', 'location')
    search_fields = ('user__username', 'service_name', 'document_name')
    readonly_fields = ('created_at',)
    def has_add_permission(self, request): return False

# --- 📄 4. SERVICE ADMIN ---
@admin.register(Service, site=admin_site)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price')

# --- 👤 5. USER PROFILE ADMIN (Full Edit, History & Reset Password) ---
@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id_link', 'full_name_display', 'mobile', 'email_display', 'user_type', 'date_joined')
    search_fields = ('fc_user_id', 'user__username', 'mobile', 'user__email', 'user__first_name')
    list_filter = ('user__is_staff', ('user__date_joined', admin.DateFieldListFilter))
    
    # Non-editable metadata and system info
    readonly_fields = ('display_fc_id', 'user_type', 'date_joined', 'action_buttons')
    
    ordering = ('-id',)

    fieldsets = (
        ('ID & Security Actions', {
            'fields': ('display_fc_id', 'user_type', 'action_buttons'),
            'description': 'System identity and administrative actions.'
        }),
        ('Personal Information (Editable)', {
            'fields': ('mobile', 'address'),
        }),
        ('System Metadata', {
            'fields': ('date_joined',)}),
    )

    def action_buttons(self, obj):
        """Generates buttons for History and Password Reset using custom admin namespace."""
        # 1. Order History URL
        history_url = (
            reverse('fastcopy_admin:core_order_changelist')
            + '?'
            + urlencode({'user__id__exact': obj.user.id})
        )
        
        # 2. Password Reset URL (Correctly namespaced to fastcopy_admin)
        password_url = reverse('fastcopy_admin:auth_user_password_change', args=[obj.user.id])
        
        return format_html(
            '<div style="display:flex; gap:10px;">'
            '<a href="{}" class="button" style="background:#2563eb; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-size:11px; font-weight:bold;">'
            '<i class="fas fa-history"></i> View Order History</a>'
            
            '<a href="{}" class="button" style="background:#be123c; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-size:11px; font-weight:bold;">'
            '<i class="fas fa-key"></i> Reset Password</a>'
            '</div>',
            history_url, password_url
        )
    action_buttons.short_description = "Administrative Actions"

    def user_id_link(self, obj):
        url = reverse('fastcopy_admin:core_userprofile_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight:bold;color:#2563eb">{}</a>', url, obj.fc_user_id or "PENDING")
    user_id_link.short_description = "User ID"
    
    def display_fc_id(self, obj): return obj.fc_user_id
    
    def full_name_display(self, obj): 
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    full_name_display.short_description = "Full Name"

    def email_display(self, obj): return obj.user.email or "N/A"
    email_display.short_description = "Email"

    def user_type(self, obj): return "Admin User" if obj.user.is_staff else "Normal User"
    def date_joined(self, obj): return obj.user.date_joined.strftime("%d %b %Y | %I:%M %p")
    def has_add_permission(self, request): return False

# --- 🚀 6. ORDER ADMIN ---
@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id_link', 
        'user_name', 
        'mobile_number',
        'service_name', 
        'display_file_thumbnail', 
        'printing_type_display', 
        'price_display', 
        'payment_status_badge', 
        'status_badge', 
        'created_at'
    )
    
    list_filter = (
        'status', 
        'payment_status', 
        ServiceTypeFilter, 
        'location', 
        ('created_at', admin.DateFieldListFilter)
    )
    
    search_fields = ('order_id', 'transaction_id', 'user__first_name', 'user__username')
    readonly_fields = ('order_id', 'created_at', 'user_name', 'user_email', 'mobile_number', 'display_full_file_preview', 'printing_type_display')
    
    fieldsets = (
        ('User Information', {'fields': ('user', 'location', 'user_name', 'mobile_number', 'user_email')}),
        ('Printing Specs', {'fields': ('service_name', 'print_mode', 'side_type', 'copies', 'custom_color_pages')}),
        ('File Management', {'fields': ('document', 'image_upload', 'display_full_file_preview')}),
        ('Financials', {'fields': ('total_price', 'transaction_id', 'payment_status')}),
        ('Workflow', {'fields': ('status', 'order_id', 'created_at')}),
    )

    def order_id_link(self, obj):
        url = reverse('fastcopy_admin:core_order_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight:bold;color:#2563eb">{}</a>', url, obj.order_id or f"ORD-{obj.id}")

    def display_file_thumbnail(self, obj):
        if obj.image_upload:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="width:35px;height:35px;object-fit:cover;border-radius:4px;"/></a>', obj.image_upload.url, obj.image_upload.url)
        elif obj.document:
            return format_html('<a href="{}" target="_blank" style="background:#2563eb;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;text-decoration:none">📂 PDF</a>', obj.document.url)
        return mark_safe('<span style="color:#94a3b8">No File</span>')

    def display_full_file_preview(self, obj):
        html = ""
        if obj.image_upload:
            html += format_html('<div style="margin-bottom:10px;"><img src="{}" style="max-width:250px;border-radius:8px;"/></div>', obj.image_upload.url)
        if obj.document:
            html += format_html('<a href="{}" target="_blank" style="background:#1e293b;color:#fff;padding:8px 12px;border-radius:5px;text-decoration:none;display:inline-block;">Open Full PDF</a>', obj.document.url)
        return mark_safe(html) if html else "No file uploaded"

    def printing_type_display(self, obj):
        mode = str(getattr(obj, 'print_mode', 'bw')).lower()
        pages = str(getattr(obj, 'custom_color_pages', '') or '')
        if 'custom' in mode and pages:
            return format_html('<b style="color:#fd7e14">CUSTOM ({})</b>', pages)
        return mode.upper()
    printing_type_display.short_description = "Mode"

    def user_name(self, obj): return obj.user.first_name
    def user_email(self, obj): return obj.user.email
    def mobile_number(self, obj): return obj.user.username 
    mobile_number.short_description = "Mobile"

    def price_display(self, obj): 
        return mark_safe(f'<b style="color:#2563eb">₹{float(obj.total_price or 0):,.2f}</b>')

    def payment_status_badge(self, obj):
        colors = {'Success': '#15803d', 'Pending': '#2563eb', 'Failed': '#be123c'}
        color = colors.get(obj.payment_status, '#64748b')
        return format_html('<span style="color:{}; font-weight:bold; font-size:10px;">{}</span>', color, obj.payment_status)
    payment_status_badge.short_description = "Payment"

    def status_badge(self, obj):
        colors = {
            'Pending': '#be123c', 'Ready': '#ca8a04', 
            'Delivered': '#15803d', 'Rejected': '#64748b', 'Cancelled': '#475569'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 10px; border-radius:12px; font-weight:bold; font-size:10px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = "Order Status"

    def changelist_view(self, request, extra_context=None):
        res = super().changelist_view(request, extra_context)
        try:
            qs = res.context_data['cl'].get_queryset(request).aggregate(total=Sum('total_price'), cnt=Count('id'))
            res.context_data.update({'summary_total': float(qs['total'] or 0), 'summary_count': qs['cnt']})
        except: pass
        return res

# --- 🛠️ 7. REGISTER AUTH MODELS TO CUSTOM SITE ---
# Registering User and Group to FastCopyAdminSite enables their URLs and password views
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)