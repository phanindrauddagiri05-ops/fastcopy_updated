# 🚀 FastCopy - Manual Deployment Guide (No GitHub Password Required)

Since you don't have your GitHub password, we will use the **Direct Upload** method. 
We will zip your code on your computer and upload it directly to the server.

Follow these steps exactly.

---

## 💻 Part 1: On Your Local Computer (Windows)

**Step 1: Zip your code**
Run this command in your VS Code terminal (PowerShell):
```powershell
git archive --format=zip --output=fastcopy.zip HEAD
```

**Step 2: Upload the zip to your server**
Run this command (it may ask for your *Server* password, not GitHub):
```powershell
scp fastcopy.zip root@64.227.174.109:/var/www/
```

**Step 3: Log in to your server**
```powershell
ssh root@64.227.174.109
```

---

## ☁️ Part 2: On The Server (After Logging In)

Once you are logged into the server (you see `root@...`), copy and paste these command blocks one by one.

### 1️⃣ Install System Software
```bash
# Update and install tools
sudo apt update -y
sudo apt install -y python3-pip python3-venv python3-dev libpq-dev nginx unzip

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2️⃣ Setup Project Files
```bash
# clear old folder if exists and recreate
rm -rf /var/www/fastcopy
mkdir -p /var/www/fastcopy

# Unzip the code
unzip /var/www/fastcopy.zip -d /var/www/fastcopy

# Go into folder
cd /var/www/fastcopy
```

### 3️⃣ Setup Python Environment
```bash
# Create virtual env
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Setup Database
python manage.py migrate
python manage.py collectstatic --noinput

# Fix Permissions
mkdir -p media staticfiles temp
chown -R www-data:www-data /var/www/fastcopy
chmod -R 775 /var/www/fastcopy
```

### 4️⃣ Create Configuration (.env)
1. Run `nano .env`
2. **Paste** this content (Right-click to paste):
```ini
SECRET_KEY=django-insecure-custom-key-12345
DEBUG=False
ALLOWED_HOSTS=fastcopies.in,www.fastcopies.in,64.227.174.109

EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_API_URL=https://api.cashfree.com/pg
```
3. Save: Press `Ctrl+X`, then `Y`, then `Enter`.

### 5️⃣ Configure Server Services
Copy-paste this **entire block** to setup Nginx and Gunicorn automatically:

```bash
# 1. Setup Gunicorn
cat > /etc/systemd/system/gunicorn.service << 'EOF'
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

# 2. Setup Nginx
cat > /etc/nginx/sites-available/fastcopy << 'EOF'
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

# 3. Apply Changes
sudo ln -sf /etc/nginx/sites-available/fastcopy /etc/nginx/sites-enabled
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 6️⃣ Setup SSL (HTTPS)
```bash
sudo apt install -y python3-certbot-nginx
sudo certbot --nginx -d fastcopies.in -d www.fastcopies.in
```

---

## 🎉 Done!
Your site should now be live at **https://fastcopies.in**
