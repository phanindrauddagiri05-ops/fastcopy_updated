#!/usr/bin/env python
"""
🔍 FastCopy Django Configuration Checker
Run this on your server to verify Django settings are loading correctly
Usage: python check_config.py
"""

import os
import sys

def check_django_config():
    print("=" * 60)
    print("🔍 FastCopy Django Configuration Checker")
    print("=" * 60)
    print()
    
    # Add project to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Set Django settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
        
        print("1️⃣ Importing Django...")
        import django
        print(f"   ✅ Django version: {django.get_version()}")
        
        print("\n2️⃣ Setting up Django...")
        django.setup()
        print("   ✅ Django setup successful")
        
        print("\n3️⃣ Loading settings...")
        from django.conf import settings
        print("   ✅ Settings loaded")
        
        print("\n4️⃣ Checking critical settings...")
        
        # Check SECRET_KEY
        if settings.SECRET_KEY and settings.SECRET_KEY != 'django-insecure-fallback-key-change-in-production':
            print(f"   ✅ SECRET_KEY: Set (length: {len(settings.SECRET_KEY)})")
        else:
            print("   ❌ SECRET_KEY: Using fallback or not set!")
            
        # Check DEBUG
        print(f"   {'⚠️ ' if settings.DEBUG else '✅'} DEBUG: {settings.DEBUG}")
        if settings.DEBUG:
            print("      WARNING: DEBUG should be False in production!")
            
        # Check ALLOWED_HOSTS
        if settings.ALLOWED_HOSTS:
            print(f"   ✅ ALLOWED_HOSTS: {', '.join(settings.ALLOWED_HOSTS)}")
        else:
            print("   ❌ ALLOWED_HOSTS: Empty!")
            
        # Check DATABASE
        db_engine = settings.DATABASES['default']['ENGINE']
        db_name = settings.DATABASES['default']['NAME']
        print(f"   ✅ DATABASE: {db_engine}")
        print(f"      File: {db_name}")
        
        # Check if database file exists
        if os.path.exists(db_name):
            print(f"      ✅ Database file exists")
            # Check if writable
            if os.access(db_name, os.W_OK):
                print(f"      ✅ Database file is writable")
            else:
                print(f"      ❌ Database file is NOT writable!")
        else:
            print(f"      ❌ Database file does NOT exist!")
            
        # Check EMAIL settings
        print(f"\n5️⃣ Email Configuration:")
        print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        if settings.EMAIL_HOST_PASSWORD:
            print(f"   ✅ EMAIL_HOST_PASSWORD: Set")
        else:
            print(f"   ❌ EMAIL_HOST_PASSWORD: Not set!")
            
        # Check CASHFREE settings
        print(f"\n6️⃣ Cashfree Configuration:")
        if settings.CASHFREE_APP_ID:
            print(f"   ✅ CASHFREE_APP_ID: Set")
        else:
            print(f"   ❌ CASHFREE_APP_ID: Not set!")
            
        if settings.CASHFREE_SECRET_KEY:
            print(f"   ✅ CASHFREE_SECRET_KEY: Set")
        else:
            print(f"   ❌ CASHFREE_SECRET_KEY: Not set!")
            
        # Check directories
        print(f"\n7️⃣ Directory Permissions:")
        for dir_name in ['media', 'staticfiles', 'temp']:
            dir_path = os.path.join(settings.BASE_DIR, dir_name)
            if os.path.exists(dir_path):
                if os.access(dir_path, os.W_OK):
                    print(f"   ✅ {dir_name}/: Exists and writable")
                else:
                    print(f"   ⚠️  {dir_name}/: Exists but NOT writable")
            else:
                print(f"   ❌ {dir_name}/: Does NOT exist")
                
        # Test database connection
        print(f"\n8️⃣ Testing Database Connection...")
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            print("   ✅ Database connection successful")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            
        # Check if migrations are applied
        print(f"\n9️⃣ Checking Migrations...")
        try:
            from django.core.management import call_command
            from io import StringIO
            
            out = StringIO()
            call_command('showmigrations', '--plan', stdout=out)
            migrations_output = out.getvalue()
            
            if '[X]' in migrations_output:
                print("   ✅ Some migrations are applied")
            else:
                print("   ⚠️  No migrations applied yet")
                print("   Run: python manage.py migrate")
        except Exception as e:
            print(f"   ⚠️  Could not check migrations: {e}")
            
        print("\n" + "=" * 60)
        print("✅ Configuration check complete!")
        print("=" * 60)
        print("\nIf you see any ❌ or ⚠️  above, fix those issues.")
        print("Then restart your web server and try again.")
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure you're running this from the project directory")
        print("and that all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    success = check_django_config()
    sys.exit(0 if success else 1)
