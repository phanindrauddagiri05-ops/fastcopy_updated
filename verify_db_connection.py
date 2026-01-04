import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
django.setup()

from django.db import connection

print("=" * 50)
print("DATABASE CONNECTION VERIFICATION")
print("=" * 50)
print(f"Database Engine: {connection.settings_dict['ENGINE']}")
print(f"Database Name: {connection.settings_dict['NAME']}")
print(f"Database User: {connection.settings_dict['USER']}")
print(f"Database Host: {connection.settings_dict['HOST']}")
print(f"Database Port: {connection.settings_dict['PORT']}")
print("=" * 50)

# Test connection
try:
    connection.ensure_connection()
    print("✓ MySQL Connection Successful!")
except Exception as e:
    print(f"✗ Connection Failed: {e}")
