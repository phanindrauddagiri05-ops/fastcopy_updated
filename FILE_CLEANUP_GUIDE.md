# 🗑️ File Cleanup System - User Guide

## 📋 Overview

The automatic file cleanup system deletes old order files (PDFs and images) while preserving all order data in the database. This prevents storage issues and keeps your server running smoothly.

---

## ✅ What Gets Deleted

### Files (Physical Storage):
- ✅ PDF documents from old orders
- ✅ Image uploads from old orders
- ✅ Temporary files older than 24 hours

### What Stays (Database):
- ✅ Order ID, user info, pricing
- ✅ Order status, dates, transaction IDs
- ✅ Complete order history
- ✅ All metadata and details

**Result:** Users can still view their complete order history, but old files are removed to free up storage.

---

## 🎯 Cleanup Rules

### Automatic Cleanup Policies:

| Order Status | File Retention Period |
|--------------|----------------------|
| Delivered | 30 days after delivery |
| Cancelled/Rejected | 7 days after cancellation |
| Failed Payment | 3 days |
| Temp Files | 24 hours |
| Pending/Confirmed/Ready | **Never deleted** |

---

## 🚀 Available Commands

### 1. View Storage Statistics
```bash
python manage.py storage_stats
```

**Shows:**
- Current storage usage by category
- Number of orders with/without files
- Cleanup potential (how much can be freed)
- Recommendations

**Example Output:**
```
📊 STORAGE STATISTICS
====================================

💾 Current Storage Usage:
  Orders (PDFs): 156.23 MB
  Orders (Images): 45.67 MB
  Temp files: 2.34 MB
  Offers: 5.12 MB
  TOTAL: 209.36 MB

🗑️  Cleanup Potential:
  Orders eligible for cleanup: 145
  Estimated storage to free: 85.5 MB

📦 Order Statistics:
  Total orders: 500
  Orders with files: 320
  Orders without files: 180
```

---

### 2. Preview Cleanup (Dry Run)
```bash
python manage.py cleanup_order_files --dry-run
```

**Features:**
- Shows what WOULD be deleted
- No actual deletion happens
- Safe to run anytime
- Use this to test before real cleanup

**Example Output:**
```
🔍 DRY RUN MODE - No files will be deleted
====================================

📊 Storage Before Cleanup:
  Orders (PDFs): 156.23 MB
  Orders (Images): 45.67 MB
  Total: 201.90 MB

🔄 Running cleanup...

✅ Cleanup Completed
====================================

📈 Cleanup Statistics:
  Orders eligible: 145
  Orders processed: 145
  Files deleted: 245
  Storage freed: 85.50 MB
  Failed deletions: 0

📁 Breakdown by File Type:
  Document: 145 files, 65.30 MB
  Image: 100 files, 20.20 MB

⚠️  This was a DRY RUN - No files were actually deleted
    Run without --dry-run to perform actual cleanup
```

---

### 3. Run Actual Cleanup
```bash
python manage.py cleanup_order_files
```

**Warning:** This will permanently delete files!

**Features:**
- Deletes files based on retention policies
- Updates database (sets file fields to NULL)
- Generates detailed report
- Logs all deletions

---

### 4. Cleanup Specific Status
```bash
# Only cleanup delivered orders
python manage.py cleanup_order_files --status=Delivered

# Only cleanup cancelled orders
python manage.py cleanup_order_files --status=Cancelled
```

---

### 5. Custom Retention Period
```bash
# Delete files older than 60 days
python manage.py cleanup_order_files --days=60

# Delete files older than 14 days
python manage.py cleanup_order_files --days=14
```

---

### 6. Cleanup Temp Files Only
```bash
python manage.py cleanup_temp_files
```

**Features:**
- Deletes files from `media/temp/` and `media/temp_img/`
- Only deletes files older than 24 hours
- Safe to run frequently

---

### 7. Skip Temp File Cleanup
```bash
python manage.py cleanup_order_files --no-temp
```

Only cleans order files, skips temporary files.

---

## ⏰ Automatic Scheduling (Production)

### Setup on Linux Server:

1. **Make script executable:**
```bash
chmod +x setup_cleanup_cron.sh
```

2. **Run setup script:**
```bash
./setup_cleanup_cron.sh
```

3. **Follow prompts to add cron jobs**

### Manual Cron Setup:

Edit crontab:
```bash
crontab -e
```

Add these lines:
```bash
# Daily cleanup at 2:00 AM
0 2 * * * cd /path/to/fastCopy && /path/to/venv/bin/python manage.py cleanup_order_files >> /path/to/logs/cleanup.log 2>&1

# Temp file cleanup every 6 hours
0 */6 * * * cd /path/to/fastCopy && /path/to/venv/bin/python manage.py cleanup_temp_files >> /path/to/logs/temp_cleanup.log 2>&1

# Weekly storage stats (Monday 9 AM)
0 9 * * 1 cd /path/to/fastCopy && /path/to/venv/bin/python manage.py storage_stats >> /path/to/logs/storage_stats.log 2>&1
```

**Replace:**
- `/path/to/fastCopy` with your project directory
- `/path/to/venv/bin/python` with your virtual environment Python path
- `/path/to/logs/` with your log directory

---

## 📊 Monitoring & Logs

### View Cleanup Logs:
```bash
# Daily cleanup log
tail -f logs/cleanup.log

# Temp cleanup log
tail -f logs/temp_cleanup.log

# Storage statistics log
tail -f logs/storage_stats.log
```

### Check Cron Jobs:
```bash
# List all cron jobs
crontab -l

# Check if cleanup is running
ps aux | grep cleanup_order_files
```

---

## 🔒 Safety Features

### 1. Dry Run Mode
Always test with `--dry-run` first to preview changes.

### 2. Protected Orders
Never deletes files from:
- Pending orders
- Confirmed orders
- Ready orders
- Orders created in last 7 days (regardless of status)

### 3. Database Preservation
- Order records are NEVER deleted
- Only file paths are set to NULL
- All metadata remains intact

### 4. Detailed Logging
Every deletion is logged with:
- Order ID
- File path
- File size
- Order status
- Age in days

---

## 💡 Best Practices

### For Development/Testing:
1. Always use `--dry-run` first
2. Check storage stats regularly
3. Test with small retention periods (e.g., `--days=1`)

### For Production:
1. Set up automatic cron jobs
2. Monitor logs weekly
3. Keep retention periods reasonable (30 days for delivered)
4. Run storage stats before major cleanups

### Recommended Schedule:
- **Daily at 2 AM:** Full cleanup
- **Every 6 hours:** Temp file cleanup
- **Weekly (Monday):** Storage statistics review

---

## 🚨 Troubleshooting

### Issue: "No module named 'core.cleanup'"
**Solution:** Make sure you're in the project directory and using the correct Python environment.

### Issue: "Permission denied" when deleting files
**Solution:** Check file permissions:
```bash
chmod -R 755 media/orders/
chown -R www-data:www-data media/orders/
```

### Issue: Cron job not running
**Solution:** 
1. Check cron service: `sudo service cron status`
2. Check cron logs: `grep CRON /var/log/syslog`
3. Verify paths in crontab are absolute

### Issue: Files not being deleted
**Solution:**
1. Run with `--dry-run` to see eligible orders
2. Check if orders meet retention criteria
3. Verify file paths exist in database

---

## 📈 Example Workflow

### Initial Setup:
```bash
# 1. Check current storage
python manage.py storage_stats

# 2. Preview cleanup
python manage.py cleanup_order_files --dry-run

# 3. Run actual cleanup
python manage.py cleanup_order_files

# 4. Verify results
python manage.py storage_stats
```

### Regular Maintenance:
```bash
# Weekly check
python manage.py storage_stats

# Monthly manual cleanup (if needed)
python manage.py cleanup_order_files --dry-run
python manage.py cleanup_order_files
```

---

## 📞 Support

### Quick Reference:
```bash
# Help for any command
python manage.py cleanup_order_files --help
python manage.py cleanup_temp_files --help
python manage.py storage_stats --help
```

### Common Commands:
```bash
# Safe preview
python manage.py cleanup_order_files --dry-run

# Actual cleanup
python manage.py cleanup_order_files

# Check storage
python manage.py storage_stats

# Clean temp files
python manage.py cleanup_temp_files
```

---

## 🎯 Summary

**What happens:**
1. ✅ Old files are automatically deleted
2. ✅ All order data stays in database
3. ✅ Users can view complete order history
4. ✅ Storage is freed up automatically
5. ✅ System runs smoothly without manual intervention

**Storage savings:**
- Typical order: 500KB - 5MB per file
- 1000 delivered orders = 500MB - 5GB saved
- Automatic cleanup prevents storage issues

**User impact:**
- ✅ Can view all order history
- ✅ Can see order details, pricing, status
- ❌ Cannot download old documents (30+ days)
- ✅ No impact on active/pending orders

---

**🚀 Ready to use! Start with `python manage.py storage_stats` to see your current storage usage.**
