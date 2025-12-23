from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from .models import Service, Order, UserProfile

class FastCopyAdminSite(admin.AdminSite):
    site_header, site_title, index_title = "FastCopy Admin", "FastCopy Portal", "Operations Hub"

admin_site = FastCopyAdminSite(name='fastcopy_admin')

@admin.register(Service, site=admin_site)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price')

@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id_link', 'full_name', 'mobile', 'email', 'user_type', 'date_joined')
    search_fields = ('fc_user_id', 'user__username', 'mobile', 'user__email')
    list_filter = ('user__is_staff', ('user__date_joined', admin.DateFieldListFilter))
    readonly_fields = ('display_fc_id', 'user_type', 'full_name', 'mobile', 'email', 'address_display', 'date_joined')
    exclude, ordering = ('user', 'fc_user_id', 'address'), ('-id',)

    fieldsets = (
        ('ID Info', {'fields': ('display_fc_id', 'user_type')}),
        ('Personal Info', {'fields': ('full_name', 'mobile', 'email', 'address_display')}),
        ('System Metadata', {'fields': ('date_joined',)}),
    )

    def user_id_link(self, obj):
        url = reverse('fastcopy_admin:core_userprofile_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight:bold;color:#2563eb">{}</a>', url, obj.fc_user_id or "PENDING")
    
    def display_fc_id(self, obj): return obj.fc_user_id
    def full_name(self, obj): return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    def email(self, obj): return obj.user.email or "N/A"
    def user_type(self, obj): return "Admin User" if obj.user.is_staff else "Normal User"
    def date_joined(self, obj): return obj.user.date_joined.strftime("%d %b %Y | %I:%M %p")
    def address_display(self, obj): return obj.address or "No address provided"
    def has_add_permission(self, request): return False

@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    # Added 'service_name' to filter list; once an order with "Custom Printing" is placed, it appears here automatically.
    list_display = ('order_id_link', 'user_name', 'service_name', 'display_document', 'mobile_number', 'printing_type_display', 'price_display', 'status_badge', 'created_at')
    list_filter = ('status', 'service_name', 'location', ('created_at', admin.DateFieldListFilter))
    search_fields = ('order_id', 'user__first_name', 'user__username')
    readonly_fields = ('order_id', 'created_at', 'user_name', 'user_email', 'mobile_number', 'display_document_large', 'printing_type_display')
    
    fieldsets = (
        ('User Information', {'fields': ('user', 'location', 'user_name', 'mobile_number', 'user_email')}),
        ('Printing Specs', {'fields': ('service_name', 'print_mode', 'side_type', 'copies', 'custom_color_pages')}),
        ('Document View', {'fields': ('document', 'display_document_large')}),
        ('Financials', {'fields': ('total_price',)}),
        ('Workflow', {'fields': ('status', 'order_id', 'created_at')}),
    )

    def order_id_link(self, obj):
        url = reverse('fastcopy_admin:core_order_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight:bold;color:#2563eb">{}</a>', url, obj.order_id or "...")

    def display_document(self, obj):
        if obj.document and obj.document.name:
            return format_html('<a href="{}" target="_blank" style="background:#2563eb;color:#fff;padding:3px 8px;border-radius:4px;font-size:10px;text-decoration:none">📂 VIEW DOC</a>', obj.document.url)
        return mark_safe('<span style="color:#94a3b8">No File</span>')

    def display_document_large(self, obj):
        return format_html('<a href="{}" target="_blank" style="background:#1e293b;color:#fff;padding:8px 12px;border-radius:5px;text-decoration:none">Preview Full Document</a>', obj.document.url) if obj.document else "No file uploaded"

    def printing_type_display(self, obj):
        mode = str(getattr(obj, 'print_mode', 'bw'))
        return format_html('<b style="color:#fd7e14">{}</b>', mode) if "(" in mode else mode.upper()

    def user_name(self, obj): return obj.user.first_name
    def user_email(self, obj): return obj.user.email
    def mobile_number(self, obj): return obj.user.username
    def price_display(self, obj): return mark_safe(f'<b style="color:#2563eb;font-size:1.1em">₹{float(obj.total_price or 0):,.2f}</b>')

    def status_badge(self, obj):
        c = {'Pending': '#be123c', 'Ready': '#ca8a04', 'Delivered': '#15803d'}.get(obj.status, '#64748b')
        return format_html('<div style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;text-align:center;width:80px;font-weight:bold">{}</div>', c, obj.status)

    def changelist_view(self, request, extra_context=None):
        res = super().changelist_view(request, extra_context)
        try:
            qs = res.context_data['cl'].get_queryset(request).aggregate(total=Sum('total_price'), cnt=Count('id'))
            res.context_data.update({'summary_total': float(qs['total'] or 0), 'summary_count': qs['cnt']})
        except: pass
        return res