"""
Quick diagnostic script to check what's in the CartItem database.
Run with: python manage.py shell < debug_cart.py
"""
from core.models import CartItem
from django.contrib.auth.models import User

print("\n=== CART ITEMS DIAGNOSTIC ===\n")

# Get all cart items
items = CartItem.objects.all()

if not items:
    print("No cart items found in database.")
else:
    for item in items:
        print(f"Cart Item ID: {item.id}")
        print(f"  User: {item.user.username}")
        print(f"  Service: {item.service_name}")
        print(f"  Print Mode: '{item.print_mode}' (type: {type(item.print_mode).__name__})")
        print(f"  Print Mode repr: {repr(item.print_mode)}")
        print(f"  Pages: {item.pages}")
        print(f"  Copies: {item.copies}")
        print(f"  Side Type: {item.side_type}")
        print(f"  Document: {item.document_name}")
        print("-" * 50)

print(f"\nTotal items: {items.count()}\n")
