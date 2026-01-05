"""
Django management command to cleanup temporary files.

Usage:
    python manage.py cleanup_temp_files
    python manage.py cleanup_temp_files --dry-run
"""

from django.core.management.base import BaseCommand
from core.cleanup import FileCleanupManager, format_bytes


class Command(BaseCommand):
    help = 'Cleanup temporary files (temp and temp_img directories)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview files to be deleted without actually deleting them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Display header
        self.stdout.write(self.style.SUCCESS('=' * 70))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No files will be deleted'))
        else:
            self.stdout.write(self.style.SUCCESS('🗑️  TEMP FILE CLEANUP'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Run cleanup
        self.stdout.write(self.style.HTTP_INFO('🔄 Cleaning temporary files...'))
        cleanup_manager = FileCleanupManager(dry_run=dry_run)
        cleanup_manager.cleanup_temp_files()

        # Display results
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Temp Cleanup Completed'))
        self.stdout.write('')
        self.stdout.write(f'  Files deleted: {len(cleanup_manager.deleted_files)}')
        self.stdout.write(f'  Storage freed: {format_bytes(cleanup_manager.total_size_freed)}')
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  This was a DRY RUN - No files were actually deleted'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Cleanup completed successfully!'))
        
        self.stdout.write('')
