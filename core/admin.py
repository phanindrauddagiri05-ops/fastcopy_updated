from django.contrib import admin
from django.db import models
from django.db.models import Sum, Count
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import Service, Order, UserProfile, CartItem, PricingConfig, Location, PublicHoliday, Coupon, PopupOffer, MaintenanceSettings

# --- 🛠️ 1. CUSTOM ADMIN SITE SETUP ---
class FastCopyAdminSite(admin.AdminSite):
    site_header = "FastCopy Administration"
    site_title = "FastCopy Admin Portal"
    index_title = "Welcome to FastCopy Management"

admin_site = FastCopyAdminSite(name='fastcopy_admin')

# --- 🔍 2. CUSTOM FILTERS ---
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

# --- 👤 5. USER PROFILE ADMIN ---
@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id_link', 'full_name_display', 'mobile', 'email_display', 'dealer_status', 'price_display', 'user_type', 'date_joined')
    search_fields = ('fc_user_id', 'user__username', 'mobile', 'user__email', 'user__first_name')
    list_filter = ('is_dealer', 'user__is_staff', ('user__date_joined', admin.DateFieldListFilter))
    readonly_fields = ('display_fc_id', 'user_type', 'date_joined', 'action_buttons')
    ordering = ('-id',)
    filter_horizontal = ('dealer_locations',)

    fieldsets = (
        ('ID & Security Actions', {'fields': ('display_fc_id', 'user_type', 'action_buttons')}),
        ('Personal Information', {'fields': ('mobile', 'address')}),
        ('Dealer & Delivery Settings', {
            'fields': ('is_dealer', 'is_delivery_boy', 'price_per_page', 'dealer_locations'),
            'description': 'Enable dealer status, delivery partner status, set custom pricing, and assign locations.'
        }),
        ('System Metadata', {'fields': ('date_joined',)}),
    )

    def action_buttons(self, obj):
        history_url = reverse('fastcopy_admin:core_order_changelist') + '?' + urlencode({'user__id__exact': obj.user.id})
        password_url = reverse('fastcopy_admin:auth_user_password_change', args=[obj.user.id])
        return format_html(
            '<div style="display:flex; gap:10px;">'
            '<a href="{}" class="button" style="background:#2563eb; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-size:11px; font-weight:bold;">View History</a>'
            '<a href="{}" class="button" style="background:#be123c; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-size:11px; font-weight:bold;">Reset Password</a>'
            '</div>', history_url, password_url
        )

    def user_id_link(self, obj):
        url = reverse('fastcopy_admin:core_userprofile_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight:bold;color:#2563eb">{}</a>', url, obj.fc_user_id or "PENDING")
    
    def display_fc_id(self, obj): return obj.fc_user_id
    def full_name_display(self, obj): return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    def email_display(self, obj): return obj.user.email or "N/A"
    def user_type(self, obj): return "Admin User" if obj.user.is_staff else "Normal User"
    def dealer_status(self, obj): 
        if obj.is_dealer:
            return format_html('<span style="background:#15803d; color:white; padding:3px 10px; border-radius:12px; font-size:10px; font-weight:bold;">DEALER</span>')
        if obj.is_delivery_boy:
            return format_html('<span style="background:#f97316; color:white; padding:3px 10px; border-radius:12px; font-size:10px; font-weight:bold;">DELIVERY</span>')
        return format_html('<span style="color:#64748b;">Customer</span>')
    def price_display(self, obj): 
        return format_html('<b style="color:#2563eb">₹{}</b>', f'{float(obj.price_per_page):.2f}')
    def date_joined(self, obj): return obj.user.date_joined.strftime("%d %b %Y | %I:%M %p")
    def has_add_permission(self, request): return False

# --- 🚀 6. ORDER ADMIN ---
@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = 'admin/core/order/change_form.html'

    list_display = (
        'order_id_link', 'user_name', 'mobile_number', 'service_name', 
        'display_file_thumbnail', 'printing_type_display', 'coupon_display',
        'price_display', 'payment_status_badge', 'status_badge', 'created_at'
    )
    
    list_filter = ('status', 'payment_status', ServiceTypeFilter, 'location', ('created_at', admin.DateFieldListFilter))
    search_fields = ('order_id', 'transaction_id', 'user__first_name', 'user__username')
    
    readonly_fields = (
        'order_id', 'created_at', 'user_name', 'user_email', 
        'mobile_number', 'document', 'image_upload', 
        'display_full_file_preview', 'printing_type_display'
    )
    
    fieldsets = (
        ('User Information', {'fields': ('user', 'location', 'user_name', 'mobile_number', 'user_email')}),
        ('Printing Specs', {'fields': ('service_name', 'print_mode', 'side_type', 'copies', 'custom_color_pages')}),
        ('File Management', {'fields': ('document', 'image_upload', 'display_full_file_preview')}),
        ('Financials', {'fields': ('original_price', 'coupon_code', 'discount_amount', 'total_price', 'transaction_id', 'payment_status')}),
        ('Workflow Metadata', {'fields': ('status', 'order_id', 'created_at')}),
    )

    def order_id_link(self, obj):
        url = reverse('fastcopy_admin:core_order_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight:bold;color:#2563eb">{}</a>', url, obj.order_id or f"ORD-{obj.id}")

    def display_file_thumbnail(self, obj):
        if obj.image_upload:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="width:35px;height:35px;object-fit:cover;border-radius:4px;"/></a>', obj.image_upload.url, obj.image_upload.url)
        elif obj.document:
            return format_html('<a href="{}" target="_blank" style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;text-decoration:none">📂 PDF</a>', obj.document.url)
        return mark_safe('<span style="color:var(--body-quiet-color)">No File</span>')

    def display_full_file_preview(self, obj):
        html = ""
        if obj.image_upload:
            html += format_html('<div style="margin-bottom:10px;"><img src="{}" style="max-width:300px;border-radius:8px;border:1px solid var(--border-color);"/></div>', obj.image_upload.url)
        if obj.document:
            html += format_html('<a href="{}" target="_blank" style="background:#1e293b;color:#fff;padding:8px 15px;border-radius:5px;text-decoration:none;display:inline-block;">👁️ View Full Document</a>', obj.document.url)
        return mark_safe(html) if html else "No file uploaded"

    def printing_type_display(self, obj):
        mode = str(getattr(obj, 'print_mode', 'bw')).upper()
        pages = getattr(obj, 'custom_color_pages', '')
        if 'CUSTOM' in mode and pages:
            return format_html('<b style="color:#fd7e14">CUSTOM ({})</b>', pages)
        return mode

    def user_name(self, obj): return obj.user.first_name if obj.user else "N/A"
    def user_email(self, obj): return obj.user.email if obj.user else "N/A"
    def mobile_number(self, obj): return obj.user.username if obj.user else "N/A"

    def price_display(self, obj): 
        return mark_safe(f'<b style="color:#2563eb">₹{float(obj.total_price or 0):,.2f}</b>')
    
    def coupon_display(self, obj):
        """Display coupon code and discount amount if applied"""
        if obj.coupon_code and obj.discount_amount and float(obj.discount_amount) > 0:
            discount_amt = float(obj.discount_amount)
            # Format the discount amount first as a string to avoid format_html issues
            discount_text = f'-₹{discount_amt:.2f}'
            return format_html(
                '<div style="display:flex; flex-direction:column; gap:2px;">'
                '<span style="background:#15803d; color:white; padding:2px 8px; border-radius:8px; font-size:10px; font-weight:bold; font-family:monospace;">{}</span>'
                '<span style="color:#15803d; font-weight:bold; font-size:11px;">{}</span>'
                '</div>',
                obj.coupon_code,
                discount_text
            )
        return format_html('<span style="color:#94a3b8; font-size:11px;">No coupon</span>')
    coupon_display.short_description = 'Coupon Applied'

    def payment_status_badge(self, obj):
        colors = {'Success': '#15803d', 'Pending': '#2563eb', 'Failed': '#be123c'}
        color = colors.get(obj.payment_status, '#64748b')
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, obj.payment_status)

    def status_badge(self, obj):
        colors = {'Pending': '#be123c', 'Ready': '#ca8a04', 'Delivered': '#15803d', 'Cancelled': '#475569'}
        color = colors.get(obj.status, '#000000')
        return format_html('<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:10px; font-weight:bold;">{}</span>', color, obj.status)

    def changelist_view(self, request, extra_context=None):
        res = super().changelist_view(request, extra_context)
        try:
            qs = res.context_data['cl'].get_queryset(request).aggregate(total=Sum('total_price'), cnt=Count('id'))
            res.context_data.update({'summary_total': float(qs['total'] or 0), 'summary_count': qs['cnt']})
        except: pass
        return res

# --- 💰 7. PRICING CONFIGURATION ADMIN ---
@admin.register(PricingConfig, site=admin_site)
class PricingConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('📄 Basic Printing Prices - Single Side (per page)', {
            'fields': (('admin_price_per_page', 'dealer_price_per_page'),),
        }),
        ('📄 Basic Printing Prices - Double Side (per page)', {
            'fields': (('admin_price_per_page_double', 'dealer_price_per_page_double'),),
        }),
        ('🌀 Spiral Binding Prices', {
            'fields': (
                'spiral_tier1_limit', ('spiral_tier1_price_admin', 'spiral_tier1_price_dealer'),
                'spiral_tier2_limit', ('spiral_tier2_price_admin', 'spiral_tier2_price_dealer'),
                'spiral_tier3_limit', ('spiral_tier3_price_admin', 'spiral_tier3_price_dealer'),
                ('spiral_extra_price_admin', 'spiral_extra_price_dealer'),
            ),
        }),
        ('📚 Soft Binding Prices', {
            'fields': (('soft_binding_price_admin', 'soft_binding_price_dealer'),),
        }),
        ('🎨 Custom Print Layout Prices', {
            'fields': (
                ('custom_1_4_price_admin', 'custom_1_4_price_dealer'),
                ('custom_1_8_price_admin', 'custom_1_8_price_dealer'),
                ('custom_1_9_price_admin', 'custom_1_9_price_dealer'),
            ),
        }),
        ('🎨 Custom Print Layout Prices - Double Side', {
            'fields': (
                ('custom_1_8_price_double_admin', 'custom_1_8_price_double_dealer'),
                ('custom_1_9_price_double_admin', 'custom_1_9_price_double_dealer'),
            ),
        }),
        ('🚚 Delivery Charges (Per Order)', {
            'fields': (('delivery_price_admin', 'delivery_price_dealer'),),
        }),
        ('🌈 Color Printing Additional Charge - Single Side', {
            'fields': (('color_price_addition_admin', 'color_price_addition_dealer'),),
        }),
        ('🌈 Color Printing Additional Charge - Double Side', {
            'fields': (('color_price_addition_admin_double', 'color_price_addition_dealer_double'),),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('__str__', 'admin_price_per_page', 'dealer_price_per_page', 'updated_at')
    
    def has_add_permission(self, request):
        return not PricingConfig.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

# --- 🎟️ 7. COUPON ADMIN ---
@admin.register(Coupon, site=admin_site)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code_display', 'discount_badge', 'validity_status', 
        'usage_display', 'min_order_display',
        'valid_from_display', 'valid_until_display'
    )
    
    list_filter = ('is_active', ('valid_from', admin.DateFieldListFilter), ('valid_until', admin.DateFieldListFilter))
    search_fields = ('code', 'description')
    
    readonly_fields = ('current_usage_count', 'created_at', 'updated_at')
    
    # Add custom form widgets for date/time fields
    formfield_overrides = {
        models.DateTimeField: {'widget': admin.widgets.AdminSplitDateTime},
    }
    
    fieldsets = (
        ('Coupon Details', {
            'fields': ('code', 'discount_percentage', 'description')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('Usage Restrictions', {
            'fields': ('minimum_order_amount', 'max_usage_count', 'current_usage_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def code_display(self, obj):
        return format_html(
            '<span style="font-family: monospace; font-weight: bold; color: #2563eb; font-size: 13px;">{}</span>',
            obj.code
        )
    code_display.short_description = 'Coupon Code'
    
    def discount_badge(self, obj):
        discount_percent = f'{float(obj.discount_percentage):.2f}'
        # Remove trailing zeros and decimal point if whole number
        if '.' in discount_percent:
            discount_percent = discount_percent.rstrip('0').rstrip('.')
        return format_html(
            '<span style="background: #15803d; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}% OFF</span>',
            discount_percent
        )
    discount_badge.short_description = 'Discount'
    
    def validity_status(self, obj):
        from django.utils import timezone
        now = timezone.now()
        
        if not obj.is_active:
            return format_html('<span style="color: #64748b;">⏸️ Inactive</span>')
        elif now < obj.valid_from:
            return format_html('<span style="color: #ca8a04;">⏳ Not Yet Active</span>')
        elif now > obj.valid_until:
            return format_html('<span style="color: #be123c;">⏰ Expired</span>')
        else:
            return format_html('<span style="color: #15803d; font-weight: bold;">✅ Active</span>')
    validity_status.short_description = 'Status'
    
    def usage_display(self, obj):
        if obj.max_usage_count == 0:
            return format_html('<span style="color: #2563eb; font-weight: bold;">{} / ∞</span>', obj.current_usage_count)
        
        percent_used = (obj.current_usage_count / obj.max_usage_count) * 100 if obj.max_usage_count > 0 else 0
        color = '#15803d' if percent_used < 50 else ('#ca8a04' if percent_used < 90 else '#be123c')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} / {}</span>',
            color, obj.current_usage_count, obj.max_usage_count
        )
    usage_display.short_description = 'Usage'
    
    def min_order_display(self, obj):
        if obj.minimum_order_amount == 0:
            return format_html('<span style="color: #64748b;">No minimum</span>')
        formatted_amount = f'{float(obj.minimum_order_amount):.2f}'
        return format_html('<span style="font-weight: bold; color: #2563eb;">₹{}</span>', formatted_amount)
    min_order_display.short_description = 'Min Order'
    
    def valid_from_display(self, obj):
        return obj.valid_from.strftime('%d %b %Y, %I:%M %p')
    valid_from_display.short_description = 'Valid From'
    
    def valid_until_display(self, obj):
        return obj.valid_until.strftime('%d %b %Y, %I:%M %p')
    valid_until_display.short_description = 'Valid Until'


# --- 🛠️ 8. REGISTER AUTH MODELS ---
admin_site.register(PublicHoliday)
admin_site.register(Location)
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)


# --- 🎁 9. POPUP OFFER ADMIN ---
@admin.register(PopupOffer, site=admin_site)
class PopupOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'status_badge', 'priority', 'start_date', 'end_date', 'thumbnail')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('title', 'description')
    ordering = ('-priority', '-created_at')
    
    fieldsets = (
        ('Offer Details', {
            'fields': ('title', 'description', 'image', 'action_url')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'priority')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date'),
            'description': 'The popup will only be valid between these dates.'
        })
    )
    
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 30px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return ""
    
    def status_badge(self, obj):
        from django.utils import timezone
        now = timezone.now()
        
        if not obj.is_active:
             return format_html('<span style="color: #64748b;">Inactive</span>')
        elif now < obj.start_date:
            return format_html('<span style="color: #ca8a04;">Scheduled</span>')
        elif now > obj.end_date:
            return format_html('<span style="color: #be123c;">Expired</span>')
        else:
            return format_html('<span style="color: #15803d; font-weight: bold;">Matches Criteria</span>')
# --- 🛠️ 10. MAINTENANCE SETTINGS ADMIN ---
@admin.register(MaintenanceSettings, site=admin_site)
class MaintenanceSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_enabled', 'expected_duration', 'updated_at')
    readonly_fields = ('updated_at',)
    
    def has_add_permission(self, request):
        # Singleton: Only allow add if no instance exists
        return not MaintenanceSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
