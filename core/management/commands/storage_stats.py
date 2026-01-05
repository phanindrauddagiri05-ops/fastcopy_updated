"""
Django management command to view storage statistics.

Usage:
    python manage.py storage_stats
"""

from django.core.management.base import BaseCommand
from core.cleanup import FileCleanupManager, format_bytes
from core.models import Order


class Command(BaseCommand):
    help = 'Display storage usage statistics'

    def handle(self, *args, **options):
        # Display header
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('📊 STORAGE STATISTICS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Get storage stats
        cleanup_manager = FileCleanupManager()
        storage_stats = cleanup_manager.get_storage_stats()

        # Display current storage
        self.stdout.write(self.style.HTTP_INFO('💾 Current Storage Usage:'))
        self.stdout.write(f'  Orders (PDFs): {storage_stats["orders_pdfs_mb"]} MB ({format_bytes(storage_stats["orders_pdfs"])})')
        self.stdout.write(f'  Orders (Images): {storage_stats["orders_images_mb"]} MB ({format_bytes(storage_stats["orders_images"])})')
        self.stdout.write(f'  Temp files: {storage_stats["temp_files_mb"]} MB ({format_bytes(storage_stats["temp_files"])})')
        self.stdout.write(f'  Offers: {storage_stats["offers_mb"]} MB ({format_bytes(storage_stats["offers"])})')
        self.stdout.write(self.style.SUCCESS(f'  TOTAL: {storage_stats["total_mb"]} MB ({format_bytes(storage_stats["total"])})'))
        self.stdout.write('')

        # Get cleanup potential
        eligible_orders = cleanup_manager.get_cleanup_eligible_orders()
        total_eligible = eligible_orders.count()
        
        # Calculate potential savings
        potential_savings = 0
        for order in eligible_orders:
            if order.document:
                try:
                    potential_savings += order.document.size
                except:
                    pass
            if order.image_upload:
                try:
                    potential_savings += order.image_upload.size
                except:
                    pass

        self.stdout.write(self.style.HTTP_INFO('🗑️  Cleanup Potential:'))
        self.stdout.write(f'  Orders eligible for cleanup: {total_eligible}')
        self.stdout.write(f'  Estimated storage to free: {format_bytes(potential_savings)}')
        self.stdout.write('')

        # Order statistics
        total_orders = Order.objects.count()
        orders_with_files = Order.objects.exclude(document='').exclude(document__isnull=True).count()
        orders_without_files = total_orders - orders_with_files

        self.stdout.write(self.style.HTTP_INFO('📦 Order Statistics:'))
        self.stdout.write(f'  Total orders: {total_orders}')
        self.stdout.write(f'  Orders with files: {orders_with_files}')
        self.stdout.write(f'  Orders without files: {orders_without_files}')
        self.stdout.write('')

        # Breakdown by status
        self.stdout.write(self.style.HTTP_INFO('📊 Orders by Status:'))
        statuses = ['Pending', 'Confirmed', 'Ready', 'Delivered', 'Rejected', 'Cancelled']
        for status in statuses:
            count = Order.objects.filter(status=status).count()
            with_files = Order.objects.filter(status=status).exclude(document='').exclude(document__isnull=True).count()
            self.stdout.write(f'  {status}: {count} orders ({with_files} with files)')
        self.stdout.write('')

        # Recommendations
        self.stdout.write(self.style.HTTP_INFO('💡 Recommendations:'))
        if total_eligible > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠️  You have {total_eligible} orders eligible for cleanup'))
            self.stdout.write(self.style.WARNING(f'  ⚠️  Run: python manage.py cleanup_order_files --dry-run'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ No cleanup needed at this time'))
        
        if storage_stats["temp_files_mb"] > 10:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Temp files are using {storage_stats["temp_files_mb"]} MB'))
            self.stdout.write(self.style.WARNING(f'  ⚠️  Run: python manage.py cleanup_temp_files'))
        
        self.stdout.write('')
