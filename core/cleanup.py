"""
File Cleanup Utility for FastCopy
Automatically deletes old order files while preserving database records.
"""

import os
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import Order
import logging

logger = logging.getLogger(__name__)


class FileCleanupManager:
    """
    Manages automatic cleanup of order files based on retention policies.
    """
    
    # Retention periods (in days)
    RETENTION_DELIVERED = 30  # Keep delivered order files for 30 days
    RETENTION_CANCELLED = 7   # Keep cancelled/rejected order files for 7 days
    RETENTION_FAILED = 3      # Keep failed payment order files for 3 days
    RETENTION_TEMP = 1        # Keep temp files for 1 day
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.deleted_files = []
        self.failed_deletions = []
        self.total_size_freed = 0
        
    def get_cleanup_eligible_orders(self, status=None, days=None):
        """
        Get orders eligible for file cleanup based on status and age.
        
        Args:
            status: Specific status to filter (optional)
            days: Custom retention days (optional)
        
        Returns:
            QuerySet of eligible orders
        """
        now = timezone.now()
        eligible_orders = Order.objects.none()
        
        # Delivered orders older than retention period
        if not status or status == 'Delivered':
            retention_days = days if days else self.RETENTION_DELIVERED
            cutoff_date = now - timedelta(days=retention_days)
            delivered_orders = Order.objects.filter(
                status='Delivered',
                updated_at__lt=cutoff_date
            ).exclude(
                document=''
            ).exclude(
                document__isnull=True
            )
            eligible_orders = eligible_orders | delivered_orders
        
        # Cancelled/Rejected orders older than retention period
        if not status or status in ['Cancelled', 'Rejected']:
            retention_days = days if days else self.RETENTION_CANCELLED
            cutoff_date = now - timedelta(days=retention_days)
            cancelled_orders = Order.objects.filter(
                status__in=['Cancelled', 'Rejected'],
                updated_at__lt=cutoff_date
            ).exclude(
                document=''
            ).exclude(
                document__isnull=True
            )
            eligible_orders = eligible_orders | cancelled_orders
        
        # Failed payment orders
        if not status or status == 'Failed':
            retention_days = days if days else self.RETENTION_FAILED
            cutoff_date = now - timedelta(days=retention_days)
            failed_orders = Order.objects.filter(
                payment_status='Failed',
                updated_at__lt=cutoff_date
            ).exclude(
                document=''
            ).exclude(
                document__isnull=True
            )
            eligible_orders = eligible_orders | failed_orders
        
        return eligible_orders.distinct()
    
    def delete_order_files(self, order):
        """
        Delete files associated with an order.
        
        Args:
            order: Order instance
        
        Returns:
            tuple: (success, files_deleted, size_freed)
        """
        files_deleted = 0
        size_freed = 0
        
        # Delete document file
        if order.document:
            file_path = order.document.path
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    
                    if not self.dry_run:
                        os.remove(file_path)
                        order.document = None
                        logger.info(f"Deleted document: {file_path} (Order: {order.order_id})")
                    else:
                        logger.info(f"[DRY RUN] Would delete: {file_path} (Order: {order.order_id})")
                    
                    files_deleted += 1
                    size_freed += file_size
                    self.deleted_files.append({
                        'order_id': order.order_id,
                        'file_path': file_path,
                        'file_type': 'document',
                        'size': file_size,
                        'status': order.status,
                        'age_days': (timezone.now() - order.updated_at).days
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to delete document {file_path}: {str(e)}")
                    self.failed_deletions.append({
                        'order_id': order.order_id,
                        'file_path': file_path,
                        'error': str(e)
                    })
        
        # Delete image file
        if order.image_upload:
            file_path = order.image_upload.path
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    
                    if not self.dry_run:
                        os.remove(file_path)
                        order.image_upload = None
                        logger.info(f"Deleted image: {file_path} (Order: {order.order_id})")
                    else:
                        logger.info(f"[DRY RUN] Would delete: {file_path} (Order: {order.order_id})")
                    
                    files_deleted += 1
                    size_freed += file_size
                    self.deleted_files.append({
                        'order_id': order.order_id,
                        'file_path': file_path,
                        'file_type': 'image',
                        'size': file_size,
                        'status': order.status,
                        'age_days': (timezone.now() - order.updated_at).days
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to delete image {file_path}: {str(e)}")
                    self.failed_deletions.append({
                        'order_id': order.order_id,
                        'file_path': file_path,
                        'error': str(e)
                    })
        
        # Save order if files were deleted
        if files_deleted > 0 and not self.dry_run:
            order.save()
        
        return files_deleted > 0, files_deleted, size_freed
    
    def cleanup_temp_files(self):
        """
        Clean up temporary files older than retention period.
        """
        media_root = settings.MEDIA_ROOT
        temp_dirs = ['temp', 'temp_img']
        
        cutoff_time = timezone.now() - timedelta(days=self.RETENTION_TEMP)
        cutoff_timestamp = cutoff_time.timestamp()
        
        for temp_dir in temp_dirs:
            temp_path = os.path.join(media_root, temp_dir)
            
            if not os.path.exists(temp_path):
                continue
            
            for filename in os.listdir(temp_path):
                file_path = os.path.join(temp_path, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_timestamp:
                        try:
                            file_size = os.path.getsize(file_path)
                            
                            if not self.dry_run:
                                os.remove(file_path)
                                logger.info(f"Deleted temp file: {file_path}")
                            else:
                                logger.info(f"[DRY RUN] Would delete temp file: {file_path}")
                            
                            self.deleted_files.append({
                                'order_id': 'N/A',
                                'file_path': file_path,
                                'file_type': 'temp',
                                'size': file_size,
                                'status': 'temp',
                                'age_days': (timezone.now().timestamp() - file_mtime) / 86400
                            })
                            self.total_size_freed += file_size
                            
                        except Exception as e:
                            logger.error(f"Failed to delete temp file {file_path}: {str(e)}")
    
    def run_cleanup(self, status=None, days=None, include_temp=True):
        """
        Run the complete cleanup process.
        
        Args:
            status: Filter by specific order status
            days: Custom retention days
            include_temp: Whether to clean temp files
        
        Returns:
            dict: Cleanup statistics
        """
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Starting file cleanup...")
        
        # Get eligible orders
        eligible_orders = self.get_cleanup_eligible_orders(status, days)
        total_orders = eligible_orders.count()
        
        logger.info(f"Found {total_orders} orders eligible for cleanup")
        
        # Process each order
        orders_processed = 0
        for order in eligible_orders:
            success, files_deleted, size_freed = self.delete_order_files(order)
            if success:
                orders_processed += 1
                self.total_size_freed += size_freed
        
        # Clean temp files
        if include_temp:
            self.cleanup_temp_files()
        
        # Generate statistics
        stats = {
            'dry_run': self.dry_run,
            'total_orders_eligible': total_orders,
            'orders_processed': orders_processed,
            'total_files_deleted': len(self.deleted_files),
            'total_size_freed': self.total_size_freed,
            'total_size_freed_mb': round(self.total_size_freed / (1024 * 1024), 2),
            'failed_deletions': len(self.failed_deletions),
            'deleted_files': self.deleted_files,
            'failed_files': self.failed_deletions,
            'timestamp': timezone.now()
        }
        
        logger.info(f"Cleanup completed: {stats['total_files_deleted']} files, "
                   f"{stats['total_size_freed_mb']} MB freed")
        
        return stats
    
    def get_storage_stats(self):
        """
        Get current storage usage statistics.
        
        Returns:
            dict: Storage statistics
        """
        media_root = settings.MEDIA_ROOT
        stats = {
            'orders_pdfs': 0,
            'orders_images': 0,
            'temp_files': 0,
            'offers': 0,
            'total': 0
        }
        
        # Calculate orders/pdfs size
        pdfs_path = os.path.join(media_root, 'orders', 'pdfs')
        if os.path.exists(pdfs_path):
            for root, dirs, files in os.walk(pdfs_path):
                stats['orders_pdfs'] += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        # Calculate orders/images size
        images_path = os.path.join(media_root, 'orders', 'images')
        if os.path.exists(images_path):
            for root, dirs, files in os.walk(images_path):
                stats['orders_images'] += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        # Calculate temp files size
        for temp_dir in ['temp', 'temp_img']:
            temp_path = os.path.join(media_root, temp_dir)
            if os.path.exists(temp_path):
                for root, dirs, files in os.walk(temp_path):
                    stats['temp_files'] += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        # Calculate offers size
        offers_path = os.path.join(media_root, 'offers')
        if os.path.exists(offers_path):
            for root, dirs, files in os.walk(offers_path):
                stats['offers'] += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        stats['total'] = sum([stats['orders_pdfs'], stats['orders_images'], 
                             stats['temp_files'], stats['offers']])
        
        # Convert to MB (create list of keys first to avoid RuntimeError)
        keys_to_convert = list(stats.keys())
        for key in keys_to_convert:
            stats[f'{key}_mb'] = round(stats[key] / (1024 * 1024), 2)
        
        return stats


def format_bytes(bytes_size):
    """
    Format bytes to human-readable format.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"
