#!/bin/bash

# FastCopy - Automatic File Cleanup Setup Script
# This script sets up automatic file cleanup using cron jobs

echo "=========================================="
echo "FastCopy - File Cleanup Setup"
echo "=========================================="
echo ""

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
MANAGE_PY="$PROJECT_DIR/manage.py"

echo "Project directory: $PROJECT_DIR"
echo "Python: $VENV_PYTHON"
echo ""

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Error: Virtual environment not found at $VENV_PYTHON"
    exit 1
fi

echo "✅ Virtual environment found"
echo ""

# Create log directory
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
echo "✅ Log directory created: $LOG_DIR"
echo ""

# Test the cleanup command
echo "🧪 Testing cleanup command (dry-run)..."
$VENV_PYTHON $MANAGE_PY cleanup_order_files --dry-run
echo ""

# Create cron job entries
CRON_FILE="/tmp/fastcopy_cron.txt"

echo "📝 Creating cron job entries..."
echo ""

cat > $CRON_FILE << EOF
# FastCopy - Automatic File Cleanup
# Generated on $(date)

# Daily cleanup of old order files at 2:00 AM
0 2 * * * cd $PROJECT_DIR && $VENV_PYTHON $MANAGE_PY cleanup_order_files >> $LOG_DIR/cleanup.log 2>&1

# Cleanup temp files every 6 hours
0 */6 * * * cd $PROJECT_DIR && $VENV_PYTHON $MANAGE_PY cleanup_temp_files >> $LOG_DIR/temp_cleanup.log 2>&1

# Weekly storage statistics report (every Monday at 9:00 AM)
0 9 * * 1 cd $PROJECT_DIR && $VENV_PYTHON $MANAGE_PY storage_stats >> $LOG_DIR/storage_stats.log 2>&1

EOF

echo "Cron jobs to be added:"
echo "----------------------------------------"
cat $CRON_FILE
echo "----------------------------------------"
echo ""

# Ask for confirmation
read -p "Do you want to add these cron jobs? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup existing crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null
    
    # Add new cron jobs
    (crontab -l 2>/dev/null; cat $CRON_FILE) | crontab -
    
    echo "✅ Cron jobs added successfully!"
    echo ""
    echo "Current crontab:"
    crontab -l
    echo ""
    echo "📋 Log files will be created in: $LOG_DIR"
    echo "   - cleanup.log (daily cleanup)"
    echo "   - temp_cleanup.log (temp file cleanup)"
    echo "   - storage_stats.log (weekly stats)"
    echo ""
else
    echo "❌ Cron job installation cancelled"
    echo ""
    echo "To manually add cron jobs, run:"
    echo "  crontab -e"
    echo ""
    echo "And add the following lines:"
    cat $CRON_FILE
fi

# Clean up
rm -f $CRON_FILE

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Available commands:"
echo "  python manage.py cleanup_order_files --dry-run    # Preview cleanup"
echo "  python manage.py cleanup_order_files              # Run cleanup"
echo "  python manage.py cleanup_temp_files               # Clean temp files"
echo "  python manage.py storage_stats                    # View statistics"
echo ""
