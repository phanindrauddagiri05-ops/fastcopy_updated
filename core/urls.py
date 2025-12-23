from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services_page, name='services'),
    path('cart/', views.cart_page, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('remove-item/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order-all/', views.order_all, name='order_all'),
    path('order-now/', views.order_now, name='order-now'),
    path('history/', views.history_view, name='history'),
    path('profile/', views.profile_view, name='profile'),
    
    # CRITICAL FIX: Ensure name matches the template
    path('profile/edit/', views.edit_profile, name='edit_profile'), 
    
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('calculate-pages/', views.calculate_pages, name='calculate_pages'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
]