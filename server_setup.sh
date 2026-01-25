#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting FastCopy Fresh Deployment...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ Please run as root (use sudo)${NC}"
  exit 1
fi

# 1. Install System Dependencies
echo -e "${GREEN}📦 Installing system dependencies...${NC}"
apt update
apt install -y python3-pip python3-venv python3-dev libpq-dev nginx unzip

# 2. Prepare /var/www/fastcopy
echo -e "${GREEN}🧹 Preparing application directory /var/www/fastcopy...${NC}"
systemctl stop gunicorn || true
rm -rf /var/www/fastcopy
mkdir -p /var/www/fastcopy

# 3. Copy Files
echo -e "${GREEN}📂 Copying files...${NC}"
cp -r . /var/www/fastcopy/
cd /var/www/fastcopy

# 4. Setup Python Environment
echo -e "${GREEN}🐍 Setting up Python Virtual Environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install gunicorn

# 5. Environment Variables
echo -e "${GREEN}⚙️ Configuring Environment...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env <<EOF
SECRET_KEY=django-insecure-$(date +%s%N)
DEBUG=False
ALLOWED_HOSTS=fastcopies.in,www.fastcopies.in,64.227.174.109
EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=CHANGE_ME
CASHFREE_APP_ID=CHANGE_ME
CASHFREE_SECRET_KEY=CHANGE_ME
CASHFREE_API_VERSION=2023-08-01
CASHFREE_API_URL=https://api.cashfree.com/pg
EOF
    echo -e "${RED}⚠️  IMPORTANT: A default .env file was created.${NC}"
    echo -e "${RED}⚠️  You MUST edit it with your real passwords after this script finishes!${NC}"
fi

# 6. Database & Static Files
echo -e "${GREEN}🗄️ Running Migrations & Collecting Static Files...${NC}"
# Force SQLite just to be safe in case env var is missing/wrong
export USE_MYSQL=False
python manage.py migrate
python manage.py collectstatic --noinput
mkdir -p media staticfiles
chown -R www-data:www-data /var/www/fastcopy
chmod -R 775 /var/www/fastcopy

# 7. Configure Gunicorn
echo -e "${GREEN}🚀 Configuring Gunicorn...${NC}"
cat > /etc/systemd/system/gunicorn.service <<EOF
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/fastcopy
ExecStart=/var/www/fastcopy/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/fastcopy/fastcopy.sock fastCopyConfig.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# 8. Configure Nginx
echo -e "${GREEN}🌐 Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/fastcopy <<EOF
server {
    listen 80;
    server_name fastcopies.in www.fastcopies.in 64.227.174.109;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /var/www/fastcopy;
    }

    location /media/ {
        root /var/www/fastcopy;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/fastcopy/fastcopy.sock;
    }
}
EOF

ln -sf /etc/nginx/sites-available/fastcopy /etc/nginx/sites-enabled
rm -f /etc/nginx/sites-enabled/default

# 9. Restart Services
echo -e "${GREEN}🔄 Restarting Services...${NC}"
systemctl daemon-reload
systemctl restart gunicorn
systemctl restart nginx
systemctl enable gunicorn
systemctl enable nginx

# 10. SSL Setup
echo -e "${GREEN}🔒 Setting up SSL (Certbot)...${NC}"
if dpkg -l | grep -q python3-certbot-nginx; then
    echo "Certbot already installed."
else
    apt install -y python3-certbot-nginx
fi
echo -e "${GREEN}⚠️  To enable HTTPS, run this command manually followed by Enter:${NC}"
echo -e "   certbot --nginx -d fastcopies.in -d www.fastcopies.in"

echo -e "${GREEN}✅ Deployment Logic Finished!${NC}"
echo -e "${RED}👉 REMINDER: Setup your .env file credentials!${NC}"
echo -e "   nano /var/www/fastcopy/.env"
