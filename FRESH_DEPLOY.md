# 🚀 FastCopy - Fresh Server Deployment Guide

This guide will take you from a fresh, empty server to a fully running website with HTTPS. 
Follow these steps exactly as written.

## 📋 Prerequisites
- A fresh Ubuntu server (Recommended: Ubuntu 22.04 or 24.04).
- Root password or SSH key.
- Your domain name (`fastcopies.in`) pointed to your server IP.

---

## 🛠️ Step 1: Connect to Your Server
Open **PowerShell** on your Windows computer and run:

```powershell
# Replace with your actual server IP
ssh root@64.227.174.109
```
*Enter your password when prompted.*

---

## 🏗️ Step 2: Install System Software
Copy and paste this entire block to update the server and install necessary software:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Git, Nginx, and database tools
sudo apt install -y python3-pip python3-venv python3-dev libpq-dev nginx curl git

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## 📂 Step 3: Clone Your Project
We will put your project in `/var/www/fastcopy`.

```bash
# Navigate to web directory
cd /var/www

# Clone the repository (Replace URL with your actual GitHub URL)
# You may need to enter your GitHub username and Personal Access Token
sudo git clone https://github.com/phanindrauddagiri05/fastcopy_updated fastcopy

# Go into the directory
cd fastcopy
```

---

## 🐍 Step 4: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

---

## ⚙️ Step 5: Configure Environment Variables

```bash
# Create .env file
nano .env
```

**Paste the following content inside (Right-click in PowerShell to paste):**
*Make sure to change `CHANGE-THIS-NOW` to a real secret key!*

```env
SECRET_KEY=django-insecure-CHANGE-THIS-NOW
DEBUG=False
ALLOWED_HOSTS=fastcopies.in,www.fastcopies.in,64.227.174.109,localhost,127.0.0.1

# Email
EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Payment
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_API_URL=https://api.cashfree.com/pg
```

**To Save & Exit:** Press `Ctrl + X`, then `Y`, then `Enter`.

---

## 🗄️ Step 6: Database & Static Files

```bash
# Run database migrations
python manage.py migrate

# Collect static files (Type 'yes' if asked)
python manage.py collectstatic

# Create required directories
mkdir -p media staticfiles temp

# Fix Permissions (Crucial!)
sudo chown -R www-data:www-data /var/www/fastcopy
sudo chmod -R 775 /var/www/fastcopy
```

---

## 🚀 Step 7: Configure Gunicorn (App Server)
This runs your Python code in the background.

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

**Paste this content:**

```ini
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
```

**Save & Exit:** `Ctrl + X`, `Y`, `Enter`.

**Start Gunicorn:**
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```
*You should see a green "active (running)" status. Press `q` to exit.*

---

## 🌐 Step 8: Configure Nginx (Web Server)
This handles web traffic and connects to Gunicorn.

```bash
sudo nano /etc/nginx/sites-available/fastcopy
```

**Paste this content:**

```nginx
server {
    listen 80;
    server_name fastcopies.in www.fastcopies.in 64.227.174.109;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/fastcopy;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        root /var/www/fastcopy;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/fastcopy/fastcopy.sock;
    }
}
```

**Save & Exit:** `Ctrl + X`, `Y`, `Enter`.

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/fastcopy /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 Step 9: Install SSL (HTTPS)

```bash
# Install Certbot
sudo apt install python3-certbot-nginx -y

# Obtain Certificate
sudo certbot --nginx -d fastcopies.in -d www.fastcopies.in
```
*Follow the prompts (Enter email, agree to terms).*

---

## 🎉 Done!
Visit **https://fastcopies.in** in your browser.

### 🆘 Troubleshooting
If something doesn't work:
```bash
# Check Gunicorn errors
journalctl -u gunicorn -f

# Check Nginx errors
tail -f /var/log/nginx/error.log
```
