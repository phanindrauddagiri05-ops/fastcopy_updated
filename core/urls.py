from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services_page, name='services'),
    path('calculate-pages/', views.calculate_pages, name='calculate_pages'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_page, name='cart'),
    path('remove-item/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order-now/', views.order_now, name='order-now'),
    path('order-all/', views.order_all, name='order_all'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]