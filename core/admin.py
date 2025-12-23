from django.contrib import admin
from django.db.models import Sum, Count, Q
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from .models import Service, Order, UserProfile

# --- 1. CUSTOM ADMIN SITE ---
class FastCopyAdminSite(admin.AdminSite):
    site_header = "FastCopy | Administrative Control Panel"
    site_title = "FastCopy Admin Portal"
    index_title = "Operational Control & Revenue Analytics"

admin_site = FastCopyAdminSite(name='fastcopy_admin')

# --- 2. ORDERS MANAGEMENT ---
class OrderAdmin(admin.ModelAdmin):
    # 2.1 Table Columns
    list_display = (
        'order_id_link', 'user_name', 'service_name', 
        'display_document', 'mobile_number', 'price_display', 
        'status_badge', 'created_at'
    )
    
    list_filter = ('status', 'service_name', ('created_at', admin.DateFieldListFilter))
    search_fields = ('order_id', 'user__first_name', 'user__username')
    readonly_fields = ('order_id', 'created_at')

    # 2.3 Detailed Order View Link
    def order_id_link(self, obj):
        url = reverse('fastcopy_admin:core_order_change', args=[obj.id])
        return format_html('<a href="{}">#{}</a>', url, obj.order_id)
    order_id_link.short_description = "Order ID"

    # NEW WAY: Robust Document Link in Table
    def display_document(self, obj):
        if obj.document and hasattr(obj.document, 'url'):
            # Check for placeholder to prevent 404
            if "default.pdf" in obj.document.name:
                return mark_safe('<span style="color: #94a3b8; font-style: italic;">No File</span>')
            
            return format_html(
                '<a href="{}" target="_blank" style="background: #2563eb; color: white; '
                'padding: 5px 10px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 10px;">'
                '📂 VIEW DOC</a>', 
                obj.document.url
            )
        return mark_safe('<span style="color: #94a3b8;">Empty</span>')
    display_document.short_description = "Document"

    def user_name(self, obj): return obj.user.first_name if obj.user else "N/A"
    
    def mobile_number(self, obj): return obj.user.username if obj.user else "N/A"
    mobile_number.short_description = "Mobile"

    # FIXED PRICE (Solves ValueError)
    def price_display(self, obj):
        try:
            return format_html("₹{:,.2f}", float(obj.total_price))
        except (ValueError, TypeError):
            return "₹0.00"
    price_display.short_description = "Price"

    def status_badge(self, obj):
        colors = {'Pending': '#be123c', 'Ready': '#ca8a04', 'Delivered': '#15803d', 'Rejected': '#64748b'}
        color = colors.get(obj.status, '#000')
        return format_html(
            '<div style="background:{}; color:white; padding:3px 10px; border-radius:12px; '
            'font-size:10px; font-weight:bold; text-align:center;">{}</div>',
            color, obj.status
        )

    # FIXED REVENUE SUMMARY (Solves ValueError)
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            cl = response.context_data['cl']
            qs = cl.get_queryset(request)
            summary = qs.aggregate(
                total_rev=Sum('total_price'),
                total_count=Count('id'),
                pending=Count('id', filter=Q(status='Pending')),
                ready=Count('id', filter=Q(status='Ready')),
                delivered=Count('id', filter=Q(status='Delivered')),
                rejected=Count('id', filter=Q(status='Rejected'))
            )
            
            extra_context = extra_context or {}
            extra_context['summary_data'] = {
                'total_revenue': float(summary['total_rev'] or 0), # RAW FLOAT
                'total_orders': summary['total_count'],
                'pending': summary['pending'],
                'ready': summary['ready'],
                'delivered': summary['delivered'],
                'rejected': summary['rejected'],
            }
            response.context_data.update(extra_context)
        except:
            pass
        return response

# Standard Registrations
admin_site.register(UserProfile)
admin_site.register(Service)
admin_site.register(Order, OrderAdmin)