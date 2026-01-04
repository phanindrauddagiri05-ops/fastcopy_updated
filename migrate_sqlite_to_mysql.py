"""
Data Migration Script: SQLite to MySQL
This script migrates all data from the old SQLite database to the new MySQL database.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')

# Import settings to modify database configuration temporarily
from django.conf import settings

print("=" * 70)
print("DATA MIGRATION: SQLite → MySQL")
print("=" * 70)

# Step 1: Connect to SQLite and export data
print("\n[1/4] Connecting to SQLite database...")
sqlite_db_path = BASE_DIR / 'fast_copy_duplic_db.sqlite3'

if not sqlite_db_path.exists():
    print(f"❌ ERROR: SQLite database not found at: {sqlite_db_path}")
    print("   Please ensure the SQLite database file exists.")
    sys.exit(1)

print(f"✓ Found SQLite database: {sqlite_db_path}")

# Temporarily switch to SQLite
original_db_config = settings.DATABASES['default'].copy()
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': sqlite_db_path,
}

# Re-initialize Django with SQLite
django.setup()

from django.core.management import call_command
from django.db import connections

# Close existing connections
connections.close_all()

print("\n[2/4] Exporting data from SQLite...")
try:
    call_command(
        'dumpdata',
        '--natural-foreign',
        '--natural-primary',
        '-e', 'contenttypes',
        '-e', 'auth.Permission',
        '--indent', '2',
        '--output', 'sqlite_data_export.json'
    )
    print("✓ Data exported to: sqlite_data_export.json")
except Exception as e:
    print(f"❌ ERROR during export: {e}")
    sys.exit(1)

# Step 2: Switch back to MySQL
print("\n[3/4] Switching to MySQL database...")
settings.DATABASES['default'] = original_db_config

# Close connections and reinitialize
connections.close_all()

# Force Django to use the new database configuration
from django.apps import apps
apps.app_configs = {}
django.setup()

print("✓ Connected to MySQL database")

# Step 3: Import data into MySQL
print("\n[4/4] Importing data into MySQL...")
try:
    call_command('loaddata', 'sqlite_data_export.json')
    print("✓ Data successfully imported to MySQL!")
except Exception as e:
    print(f"❌ ERROR during import: {e}")
    print("\nThis might happen if:")
    print("  - MySQL tables don't exist (run: python manage.py migrate)")
    print("  - Data conflicts with existing MySQL data")
    print("  - Foreign key constraints are violated")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ MIGRATION COMPLETE!")
print("=" * 70)
print("\nNext steps:")
print("1. Verify data in MySQL: venv\\Scripts\\python.exe check_dealer_orders.py")
print("2. Test the application: venv\\Scripts\\python.exe manage.py runserver")
print("3. Backup the SQLite file: fast_copy_duplic_db.sqlite3")
print("=" * 70)
