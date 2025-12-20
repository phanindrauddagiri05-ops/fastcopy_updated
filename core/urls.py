from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services_page, name='services'),
    path('calculate-pages/', views.calculate_pages, name='calculate_pages'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    
    # Cart Paths
    path('cart/', views.cart_page, name='cart'),
    path('remove-item/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Order Paths
    path('order-now/', views.order_now, name='order-now'),
    # FIX: Renamed name to 'order_all' to match your cart.html template
    path('process-cart-order/', views.process_cart_order, name='order_all'),
    
    # Profile & Auth
    path('profile/', views.profile_view, name='profile'),
    path('history/', views.history_view, name='history'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]