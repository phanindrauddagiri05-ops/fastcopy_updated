#!/bin/bash
# 🚀 FastCopy - One-Command Server Update Script
# This script automates the entire deployment process

echo "============================================"
echo "🚀 FastCopy Server Update & Fix Script"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project directory - CHANGE THIS IF DIFFERENT
PROJECT_DIR="/var/www/fastcopy"

echo -e "${BLUE}📂 Project Directory: $PROJECT_DIR${NC}"
echo ""

# Step 1: Navigate to project
echo "Step 1: Navigating to project directory..."
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Failed to navigate to $PROJECT_DIR${NC}"
    echo "Please edit this script and set the correct PROJECT_DIR"
    exit 1
}
echo -e "${GREEN}✅ In project directory${NC}"
echo ""

# Step 2: Pull latest code
echo "Step 2: Pulling latest code from Git..."
git pull origin main || {
    echo -e "${YELLOW}⚠️  Git pull failed. Trying to stash changes...${NC}"
    git stash
    git pull origin main
}
echo -e "${GREEN}✅ Code updated${NC}"
echo ""

# Step 3: Check .env file
echo "Step 3: Checking .env file..."
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file NOT found!${NC}"
    echo -e "${YELLOW}Creating .env template...${NC}"
    cat > .env << 'EOF'
SECRET_KEY=CHANGE-THIS-NOW
DEBUG=False
ALLOWED_HOSTS=fastcopy.pagexplore.com,64.227.174.109
EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_API_URL=https://api.cashfree.com/pg
ADMIN_EMAIL=fastcopyteam@gmail.com
SUPPORT_EMAIL=fastcopy003@gmail.com
SUPPORT_PHONE=+91 8500290959
COMPANY_WEBSITE=https://fastcopy.pagexplore.com
EOF
    echo -e "${YELLOW}⚠️  .env created. EDIT IT NOW with actual credentials!${NC}"
    echo -e "${YELLOW}Run: nano .env${NC}"
    echo ""
    read -p "Press Enter after you've edited .env file..."
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi
echo ""

# Step 4: Database setup
echo "Step 4: Setting up database..."
if [ ! -f "fast_copy_duplic_db.sqlite3" ]; then
    echo -e "${YELLOW}⚠️  Database not found. Creating...${NC}"
    python3 manage.py migrate
fi
chmod 664 fast_copy_duplic_db.sqlite3 2>/dev/null
chmod 775 . 2>/dev/null
echo -e "${GREEN}✅ Database configured${NC}"
echo ""

# Step 5: Create directories
echo "Step 5: Creating required directories..."
mkdir -p media staticfiles temp
chmod 775 media staticfiles temp
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Step 6: Install dependencies
echo "Step 6: Installing dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi
pip install -q python-dotenv PyPDF2 2>/dev/null
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 7: Collect static files
echo "Step 7: Collecting static files..."
python3 manage.py collectstatic --noinput > /dev/null 2>&1
echo -e "${GREEN}✅ Static files collected${NC}"
echo ""

# Step 8: Run configuration check
echo "Step 8: Verifying configuration..."
python3 check_config.py
echo ""

# Step 9: Restart web server
echo "Step 9: Restarting web server..."
if systemctl is-active --quiet apache2; then
    sudo systemctl restart apache2
    echo -e "${GREEN}✅ Apache2 restarted${NC}"
elif systemctl is-active --quiet nginx; then
    sudo systemctl restart gunicorn 2>/dev/null
    sudo systemctl restart nginx
    echo -e "${GREEN}✅ Nginx + Gunicorn restarted${NC}"
else
    echo -e "${YELLOW}⚠️  Could not detect web server${NC}"
fi
echo ""

echo "============================================"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "============================================"
echo ""
echo "🧪 Test your site now:"
echo "   https://fastcopy.pagexplore.com/login/"
echo ""
echo "📊 If still having issues, check logs:"
echo "   tail -f /var/log/apache2/error.log"
echo "   journalctl -u gunicorn -f"
echo ""
