#!/bin/bash
# 🚀 FastCopy Server Error 500 - Quick Fix Script
# Run this on your server to diagnose and fix common issues

echo "============================================"
echo "🔍 FastCopy Server Diagnostic Script"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Find project directory (adjust this path to your actual project location)
# Common locations: /var/www/fastcopy, /home/username/fastcopy, /opt/fastcopy
PROJECT_DIR="/var/www/fastcopy"  # CHANGE THIS TO YOUR ACTUAL PATH

echo "📁 Checking project directory: $PROJECT_DIR"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Project directory not found!${NC}"
    echo "Please edit this script and set PROJECT_DIR to your actual project path"
    exit 1
fi

cd "$PROJECT_DIR" || exit

echo -e "${GREEN}✅ Project directory found${NC}"
echo ""

# Check 1: .env file
echo "============================================"
echo "1️⃣ Checking .env file..."
echo "============================================"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    echo "Checking for required variables..."
    
    if grep -q "SECRET_KEY=" .env; then
        echo -e "${GREEN}  ✅ SECRET_KEY found${NC}"
    else
        echo -e "${RED}  ❌ SECRET_KEY missing${NC}"
    fi
    
    if grep -q "EMAIL_HOST_PASSWORD=" .env; then
        echo -e "${GREEN}  ✅ EMAIL_HOST_PASSWORD found${NC}"
    else
        echo -e "${YELLOW}  ⚠️  EMAIL_HOST_PASSWORD missing${NC}"
    fi
    
    if grep -q "CASHFREE_APP_ID=" .env; then
        echo -e "${GREEN}  ✅ CASHFREE_APP_ID found${NC}"
    else
        echo -e "${YELLOW}  ⚠️  CASHFREE_APP_ID missing${NC}"
    fi
else
    echo -e "${RED}❌ .env file NOT found!${NC}"
    echo "Creating .env template..."
    cat > .env << 'EOF'
SECRET_KEY=django-insecure-CHANGE-THIS-NOW
DEBUG=False
ALLOWED_HOSTS=fastcopies.in,www.fastcopies.in,64.227.174.109
EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_API_URL=https://api.cashfree.com/pg
ADMIN_EMAIL=fastcopyteam@gmail.com
SUPPORT_EMAIL=fastcopy003@gmail.com
SUPPORT_PHONE=+91 8500290959
COMPANY_WEBSITE=https://fastcopies.in
EOF
    echo -e "${YELLOW}⚠️  .env template created. PLEASE EDIT IT WITH ACTUAL VALUES!${NC}"
fi
echo ""

# Check 2: Database
echo "============================================"
echo "2️⃣ Checking database..."
echo "============================================"
if [ -f "fast_copy_duplic_db.sqlite3" ]; then
    echo -e "${GREEN}✅ Database file exists${NC}"
    ls -lh fast_copy_duplic_db.sqlite3
    
    # Check permissions
    if [ -w "fast_copy_duplic_db.sqlite3" ]; then
        echo -e "${GREEN}✅ Database is writable${NC}"
    else
        echo -e "${RED}❌ Database is NOT writable${NC}"
        echo "Fixing permissions..."
        chmod 664 fast_copy_duplic_db.sqlite3
        echo -e "${GREEN}✅ Permissions fixed${NC}"
    fi
else
    echo -e "${RED}❌ Database file NOT found!${NC}"
    echo "Run: python manage.py migrate"
fi
echo ""

# Check 3: Required directories
echo "============================================"
echo "3️⃣ Checking required directories..."
echo "============================================"
for dir in media staticfiles temp; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $dir/ exists${NC}"
    else
        echo -e "${YELLOW}⚠️  $dir/ missing - creating...${NC}"
        mkdir -p "$dir"
        chmod 775 "$dir"
        echo -e "${GREEN}✅ $dir/ created${NC}"
    fi
done
echo ""

# Check 4: Python environment
echo "============================================"
echo "4️⃣ Checking Python environment..."
echo "============================================"
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    source venv/bin/activate
    
    # Check critical packages
    echo "Checking critical packages..."
    python -c "import django" 2>/dev/null && echo -e "${GREEN}  ✅ Django installed${NC}" || echo -e "${RED}  ❌ Django missing${NC}"
    python -c "import dotenv" 2>/dev/null && echo -e "${GREEN}  ✅ python-dotenv installed${NC}" || echo -e "${RED}  ❌ python-dotenv missing${NC}"
    python -c "import PyPDF2" 2>/dev/null && echo -e "${GREEN}  ✅ PyPDF2 installed${NC}" || echo -e "${YELLOW}  ⚠️  PyPDF2 missing${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "Checking system Python..."
    python3 --version
fi
echo ""

# Check 5: Web server
echo "============================================"
echo "5️⃣ Checking web server status..."
echo "============================================"
if systemctl is-active --quiet apache2; then
    echo -e "${GREEN}✅ Apache2 is running${NC}"
    WEB_SERVER="apache2"
elif systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx is running${NC}"
    WEB_SERVER="nginx"
    if systemctl is-active --quiet gunicorn; then
        echo -e "${GREEN}✅ Gunicorn is running${NC}"
    else
        echo -e "${RED}❌ Gunicorn is NOT running${NC}"
    fi
else
    echo -e "${RED}❌ No web server detected${NC}"
    WEB_SERVER=""
fi
echo ""

# Summary and recommendations
echo "============================================"
echo "📋 SUMMARY & NEXT STEPS"
echo "============================================"
echo ""
echo "1. Edit .env file with actual credentials:"
echo "   nano .env"
echo ""
echo "2. If database was missing, run migrations:"
echo "   python manage.py migrate"
echo ""
echo "3. Collect static files:"
echo "   python manage.py collectstatic --noinput"
echo ""
echo "4. Restart web server:"
if [ "$WEB_SERVER" = "apache2" ]; then
    echo "   sudo systemctl restart apache2"
elif [ "$WEB_SERVER" = "nginx" ]; then
    echo "   sudo systemctl restart gunicorn"
    echo "   sudo systemctl restart nginx"
fi
echo ""
echo "5. Check error logs:"
if [ "$WEB_SERVER" = "apache2" ]; then
    echo "   tail -f /var/log/apache2/error.log"
elif [ "$WEB_SERVER" = "nginx" ]; then
    echo "   journalctl -u gunicorn -f"
fi
echo ""
echo "============================================"
echo "🔍 To see detailed error, temporarily enable DEBUG:"
echo "   1. Edit .env: nano .env"
echo "   2. Set: DEBUG=True"
echo "   3. Restart server"
echo "   4. Try login again to see exact error"
echo "   5. Set DEBUG=False after fixing!"
echo "============================================"
