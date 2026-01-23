from django.urls import path
from . import views

urlpatterns = [
    # --- 🏠 Home & Static ---
    path('', views.home, name='home'),
    path('services/', views.services_page, name='services'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_conditions, name='terms_conditions'),

    # --- 👤 Auth & Profile ---
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password_request, name='forgot_password'),
    path('forgot-password/sent/', views.forgot_password_sent, name='forgot_password_sent'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    path('history/', views.history_view, name='history'),

    # --- 🛒 Cart Logic ---
    path('cart/', views.cart_page, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('calculate-pages/', views.calculate_pages, name='calculate_pages'),

    # --- 🚀 Checkout & Orders ---
    # order_now: Path for Service Page "Order Now" (Direct)
    path('order/now/', views.order_now, name='order_now'),
    
    # process_direct_order: AJAX handler for Service Page validation
    path('order/direct/', views.process_direct_order, name='process_direct_order'), 
    
    # order_all: Path for Cart Page "Order All" (Cart-based)
    path('order/process-all/', views.order_all, name='order_all'),
    
    # checkout_summary: Displays either Direct Item or Cart Items based on source prefix
    path('checkout/summary/', views.cart_checkout_summary, name='cart_checkout_summary'),

    # --- 🎟️ Coupons ---
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),

    # --- 💳 Payments ---
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/cashfree-checkout/', views.cashfree_checkout, name='cashfree_checkout'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),    

    # --- 🏪 Dealer Dashboard ---
    path('dealer/login/', views.dealer_login_view, name='dealer_login'),
    path('dealer/dashboard/', views.dealer_dashboard_view, name='dealer_dashboard'),
    path('dealer/logout/', views.dealer_logout_view, name='dealer_logout'),
    path('dealer/update-order/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('dealer/download/<int:order_id>/', views.dealer_download_file, name='dealer_download_file'),
    # --- 🛠️ 10. MAINTENANCE ---
    path('maintenance/', views.maintenance_view, name='maintenance'),
]