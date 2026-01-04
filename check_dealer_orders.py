import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
django.setup()

from core.models import Order, UserProfile, Location
from django.contrib.auth.models import User

print("=" * 60)
print("DEALER ORDERS DIAGNOSTIC")
print("=" * 60)

# Check dealers
dealers = UserProfile.objects.filter(is_dealer=True)
print(f"\n📊 Total Dealers: {dealers.count()}")
for dealer in dealers:
    print(f"\n  Dealer: {dealer.user.username} ({dealer.user.first_name})")
    print(f"  Locations assigned: {list(dealer.dealer_locations.values_list('name', flat=True))}")

# Check locations
locations = Location.objects.all()
print(f"\n📍 Total Locations: {locations.count()}")
for loc in locations:
    print(f"  - {loc.name}")

# Check orders
orders = Order.objects.filter(payment_status='Success')
print(f"\n📦 Total Successful Orders: {orders.count()}")
print(f"\nOrders by location:")
for loc_name in orders.values_list('location', flat=True).distinct():
    count = orders.filter(location=loc_name).count()
    print(f"  - {loc_name or '(No location)'}: {count} orders")

# Check if dealers can see orders
print("\n" + "=" * 60)
print("DEALER ORDER VISIBILITY")
print("=" * 60)
for dealer in dealers:
    if dealer.dealer_locations.exists():
        loc_names = list(dealer.dealer_locations.values_list('name', flat=True))
        dealer_orders = orders.filter(location__in=loc_names)
        print(f"\n  Dealer: {dealer.user.username}")
        print(f"  Assigned locations: {loc_names}")
        print(f"  Visible orders: {dealer_orders.count()}")
    else:
        print(f"\n  Dealer: {dealer.user.username}")
        print(f"  ⚠️  NO LOCATIONS ASSIGNED - Cannot see any orders!")

print("\n" + "=" * 60)
