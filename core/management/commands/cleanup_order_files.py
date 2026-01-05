"""
Django management command to cleanup old order files.

Usage:
    python manage.py cleanup_order_files
    python manage.py cleanup_order_files --dry-run
    python manage.py cleanup_order_files --status=delivered
    python manage.py cleanup_order_files --days=30
    python manage.py cleanup_order_files --no-temp
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from core.cleanup import FileCleanupManager, format_bytes
from datetime import datetime


class Command(BaseCommand):
    help = 'Cleanup old order files while preserving database records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview files to be deleted without actually deleting them',
        )
        parser.add_argument(
            '--status',
            type=str,
            help='Filter by specific order status (Delivered, Cancelled, Rejected, Failed)',
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Custom retention period in days',
        )
        parser.add_argument(
            '--no-temp',
            action='store_true',
            help='Skip cleaning temporary files',
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send cleanup report via email to admin',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        status = options['status']
        days = options['days']
        include_temp = not options['no_temp']
        send_email = options['send_email']

        # Display header
        self.stdout.write(self.style.SUCCESS('=' * 70))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No files will be deleted'))
        else:
            self.stdout.write(self.style.SUCCESS('🗑️  FILE CLEANUP - Starting cleanup process'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Show configuration
        self.stdout.write(self.style.HTTP_INFO('Configuration:'))
        if status:
            self.stdout.write(f'  Status filter: {status}')
        if days:
            self.stdout.write(f'  Retention days: {days}')
        else:
            self.stdout.write(f'  Retention days: Default (Delivered: 30, Cancelled: 7, Failed: 3)')
        self.stdout.write(f'  Include temp files: {include_temp}')
        self.stdout.write('')

        # Get storage stats before cleanup
        self.stdout.write(self.style.HTTP_INFO('📊 Storage Before Cleanup:'))
        cleanup_manager = FileCleanupManager(dry_run=dry_run)
        storage_stats = cleanup_manager.get_storage_stats()
        
        self.stdout.write(f'  Orders (PDFs): {storage_stats["orders_pdfs_mb"]} MB')
        self.stdout.write(f'  Orders (Images): {storage_stats["orders_images_mb"]} MB')
        self.stdout.write(f'  Temp files: {storage_stats["temp_files_mb"]} MB')
        self.stdout.write(f'  Offers: {storage_stats["offers_mb"]} MB')
        self.stdout.write(f'  Total: {storage_stats["total_mb"]} MB')
        self.stdout.write('')

        # Run cleanup
        self.stdout.write(self.style.HTTP_INFO('🔄 Running cleanup...'))
        stats = cleanup_manager.run_cleanup(
            status=status,
            days=days,
            include_temp=include_temp
        )

        # Display results
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ Cleanup Completed'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        self.stdout.write(self.style.HTTP_INFO('📈 Cleanup Statistics:'))
        self.stdout.write(f'  Orders eligible: {stats["total_orders_eligible"]}')
        self.stdout.write(f'  Orders processed: {stats["orders_processed"]}')
        self.stdout.write(f'  Files deleted: {stats["total_files_deleted"]}')
        self.stdout.write(f'  Storage freed: {stats["total_size_freed_mb"]} MB ({format_bytes(stats["total_size_freed"])})')
        self.stdout.write(f'  Failed deletions: {stats["failed_deletions"]}')
        self.stdout.write('')

        # Show breakdown by file type
        if stats['deleted_files']:
            file_types = {}
            for file_info in stats['deleted_files']:
                file_type = file_info['file_type']
                if file_type not in file_types:
                    file_types[file_type] = {'count': 0, 'size': 0}
                file_types[file_type]['count'] += 1
                file_types[file_type]['size'] += file_info['size']

            self.stdout.write(self.style.HTTP_INFO('📁 Breakdown by File Type:'))
            for file_type, data in file_types.items():
                size_mb = round(data['size'] / (1024 * 1024), 2)
                self.stdout.write(f'  {file_type.capitalize()}: {data["count"]} files, {size_mb} MB')
            self.stdout.write('')

        # Show breakdown by order status
        if stats['deleted_files']:
            status_breakdown = {}
            for file_info in stats['deleted_files']:
                order_status = file_info['status']
                if order_status not in status_breakdown:
                    status_breakdown[order_status] = {'count': 0, 'size': 0}
                status_breakdown[order_status]['count'] += 1
                status_breakdown[order_status]['size'] += file_info['size']

            self.stdout.write(self.style.HTTP_INFO('📊 Breakdown by Order Status:'))
            for order_status, data in status_breakdown.items():
                size_mb = round(data['size'] / (1024 * 1024), 2)
                self.stdout.write(f'  {order_status}: {data["count"]} files, {size_mb} MB')
            self.stdout.write('')

        # Show failed deletions
        if stats['failed_files']:
            self.stdout.write(self.style.ERROR('❌ Failed Deletions:'))
            for failed in stats['failed_files'][:10]:  # Show first 10
                self.stdout.write(f'  Order: {failed["order_id"]} - {failed["error"]}')
            if len(stats['failed_files']) > 10:
                self.stdout.write(f'  ... and {len(stats["failed_files"]) - 10} more')
            self.stdout.write('')

        # Get storage stats after cleanup
        if not dry_run:
            self.stdout.write(self.style.HTTP_INFO('📊 Storage After Cleanup:'))
            storage_stats_after = cleanup_manager.get_storage_stats()
            self.stdout.write(f'  Orders (PDFs): {storage_stats_after["orders_pdfs_mb"]} MB')
            self.stdout.write(f'  Orders (Images): {storage_stats_after["orders_images_mb"]} MB')
            self.stdout.write(f'  Temp files: {storage_stats_after["temp_files_mb"]} MB')
            self.stdout.write(f'  Total: {storage_stats_after["total_mb"]} MB')
            self.stdout.write('')

        # Send email report
        if send_email and not dry_run:
            self.send_email_report(stats, storage_stats)

        # Final message
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  This was a DRY RUN - No files were actually deleted'))
            self.stdout.write(self.style.WARNING('    Run without --dry-run to perform actual cleanup'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Cleanup completed successfully!'))
        
        self.stdout.write('')

    def send_email_report(self, stats, storage_stats):
        """Send cleanup report via email"""
        subject = f"FastCopy - File Cleanup Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        message = f"""
FastCopy File Cleanup Report
============================

Cleanup completed successfully!

Statistics:
-----------
Orders eligible: {stats['total_orders_eligible']}
Orders processed: {stats['orders_processed']}
Files deleted: {stats['total_files_deleted']}
Storage freed: {stats['total_size_freed_mb']} MB
Failed deletions: {stats['failed_deletions']}

Storage Before Cleanup:
----------------------
Orders (PDFs): {storage_stats['orders_pdfs_mb']} MB
Orders (Images): {storage_stats['orders_images_mb']} MB
Temp files: {storage_stats['temp_files_mb']} MB
Total: {storage_stats['total_mb']} MB

Timestamp: {stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

Next cleanup: Tomorrow at 2:00 AM
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else ['admin@fastcopy.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('📧 Email report sent successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send email: {str(e)}'))
