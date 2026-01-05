"""
Admin views for file cleanup monitoring and control.
"""

from django.contrib import admin
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .cleanup import FileCleanupManager, format_bytes
from .models import Order
import json


@staff_member_required
def cleanup_dashboard(request):
    """
    Main dashboard for file cleanup monitoring and control.
    """
    cleanup_manager = FileCleanupManager()
    
    # Get storage statistics
    storage_stats = cleanup_manager.get_storage_stats()
    
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
    
    # Order statistics
    total_orders = Order.objects.count()
    orders_with_files = Order.objects.exclude(document='').exclude(document__isnull=True).count()
    orders_without_files = total_orders - orders_with_files
    
    # Breakdown by status
    status_breakdown = []
    statuses = ['Pending', 'Confirmed', 'Ready', 'Delivered', 'Rejected', 'Cancelled']
    for status in statuses:
        count = Order.objects.filter(status=status).count()
        with_files = Order.objects.filter(status=status).exclude(document='').exclude(document__isnull=True).count()
        status_breakdown.append({
            'status': status,
            'total': count,
            'with_files': with_files,
            'without_files': count - with_files
        })
    
    context = {
        'storage_stats': storage_stats,
        'total_eligible': total_eligible,
        'potential_savings': potential_savings,
        'potential_savings_mb': round(potential_savings / (1024 * 1024), 2),
        'total_orders': total_orders,
        'orders_with_files': orders_with_files,
        'orders_without_files': orders_without_files,
        'status_breakdown': status_breakdown,
        'retention_policies': {
            'delivered': FileCleanupManager.RETENTION_DELIVERED,
            'cancelled': FileCleanupManager.RETENTION_CANCELLED,
            'failed': FileCleanupManager.RETENTION_FAILED,
            'temp': FileCleanupManager.RETENTION_TEMP,
        }
    }
    
    return render(request, 'admin/cleanup_dashboard.html', context)


@staff_member_required
@require_http_methods(["POST"])
def run_cleanup_ajax(request):
    """
    AJAX endpoint to run cleanup.
    """
    try:
        data = json.loads(request.body)
        dry_run = data.get('dry_run', True)
        status = data.get('status', None)
        days = data.get('days', None)
        include_temp = data.get('include_temp', True)
        
        # Run cleanup
        cleanup_manager = FileCleanupManager(dry_run=dry_run)
        stats = cleanup_manager.run_cleanup(
            status=status,
            days=int(days) if days else None,
            include_temp=include_temp
        )
        
        # Convert datetime to string for JSON serialization
        stats['timestamp'] = stats['timestamp'].isoformat()
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'message': 'Cleanup completed successfully' if not dry_run else 'Dry run completed'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
def refresh_storage_stats(request):
    """
    AJAX endpoint to refresh storage statistics.
    """
    try:
        cleanup_manager = FileCleanupManager()
        storage_stats = cleanup_manager.get_storage_stats()
        
        # Get cleanup potential
        eligible_orders = cleanup_manager.get_cleanup_eligible_orders()
        total_eligible = eligible_orders.count()
        
        return JsonResponse({
            'success': True,
            'storage_stats': storage_stats,
            'total_eligible': total_eligible
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
def download_cleanup_report(request):
    """
    Download cleanup report as text file.
    """
    cleanup_manager = FileCleanupManager(dry_run=True)
    stats = cleanup_manager.run_cleanup()
    
    # Generate report
    report = f"""
FastCopy - File Cleanup Report
Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 70}

STORAGE STATISTICS
------------------
Orders (PDFs): {stats.get('storage_stats', {}).get('orders_pdfs_mb', 0)} MB
Orders (Images): {stats.get('storage_stats', {}).get('orders_images_mb', 0)} MB
Temp Files: {stats.get('storage_stats', {}).get('temp_files_mb', 0)} MB
Total: {stats.get('storage_stats', {}).get('total_mb', 0)} MB

CLEANUP POTENTIAL
-----------------
Orders eligible: {stats['total_orders_eligible']}
Files to delete: {stats['total_files_deleted']}
Storage to free: {stats['total_size_freed_mb']} MB

RETENTION POLICIES
------------------
Delivered orders: {FileCleanupManager.RETENTION_DELIVERED} days
Cancelled orders: {FileCleanupManager.RETENTION_CANCELLED} days
Failed orders: {FileCleanupManager.RETENTION_FAILED} days
Temp files: {FileCleanupManager.RETENTION_TEMP} day(s)

{'=' * 70}
This is a preview report. No files were deleted.
Run actual cleanup from the admin dashboard.
"""
    
    response = HttpResponse(report, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="cleanup_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'
    return response
