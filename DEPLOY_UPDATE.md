# 🚀 FastCopy - Server Update Deployment Guide

## 📋 Step-by-Step Instructions to Update Your Server

Follow these steps **in order** to update your server with the latest code and fix the 500 error.

---

## 🔐 Step 1: SSH into Your Server

```bash
ssh root@64.227.174.109
# Or: ssh username@64.227.174.109
```

Enter your server password when prompted.

---

## 📂 Step 2: Navigate to Project Directory

```bash
cd /var/www/fastcopy
# Or wherever your project is deployed
# Common locations: /home/username/fastcopy, /opt/fastcopy
```

**Verify you're in the right directory:**
```bash
pwd
ls -la
# You should see: manage.py, fastCopyConfig/, core/, etc.
```

---

## 🔄 Step 3: Pull Latest Code from Git

```bash
# Pull the latest changes
git pull origin main
```

**Expected output:**
```
Updating 2f8b834..8b3fcd9
Fast-forward
 .env.example           | 31 +++++++++++
 QUICK_FIX.md          | 123 +++++++++++++++++++++++++++++++++++++
 check_config.py       | 156 +++++++++++++++++++++++++++++++++++++++++++++
 fix_server.sh         | 198 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 server_diagnostic.md  | 302 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 6 files changed, 810 insertions(+)
```

---

## 🔍 Step 4: Run Diagnostic Script

```bash
# Make the script executable
chmod +x fix_server.sh

# Run the diagnostic
bash fix_server.sh
```

**This will check:**
- ✅ .env file existence
- ✅ Database file and permissions
- ✅ Required directories
- ✅ Python packages
- ✅ Web server status

**Take note of any ❌ or ⚠️ warnings!**

---

## 🔧 Step 5: Create/Edit .env File

This is the **MOST IMPORTANT** step!

```bash
# Check if .env exists
ls -la .env

# If it doesn't exist, create it
nano .env
```

**Paste this content and REPLACE with your actual values:**

```env
SECRET_KEY=django-insecure-CHANGE-THIS-TO-RANDOM-SECRET-KEY
DEBUG=False
ALLOWED_HOSTS=fastcopies.in,64.227.174.109,www.fastcopies.in

# Email Configuration
EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=your-actual-gmail-app-password

# Cashfree Payment Gateway
CASHFREE_APP_ID=your-actual-cashfree-app-id
CASHFREE_SECRET_KEY=your-actual-cashfree-secret-key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_API_URL=https://api.cashfree.com/pg

# Company Details
ADMIN_EMAIL=fastcopyteam@gmail.com
SUPPORT_EMAIL=fastcopy003@gmail.com
SUPPORT_PHONE=+91 8500290959
COMPANY_WEBSITE=https://fastcopies.in
```

**To save in nano:**
- Press `Ctrl + X`
- Press `Y` (Yes)
- Press `Enter`

### 🔑 Generate a Strong SECRET_KEY

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it as your `SECRET_KEY` in the `.env` file.

---

## 🗄️ Step 6: Verify Database

```bash
# Check if database exists
ls -la fast_copy_duplic_db.sqlite3

# If it doesn't exist, create it
python3 manage.py migrate

# Fix permissions
chmod 664 fast_copy_duplic_db.sqlite3
chmod 775 .
```

---

## 📁 Step 7: Create Required Directories

```bash
# Create directories if they don't exist
mkdir -p media staticfiles temp

# Set proper permissions
chmod 775 media staticfiles temp

# Verify
ls -la | grep -E "media|staticfiles|temp"
```

---

## 📦 Step 8: Install/Update Dependencies

```bash
# Activate virtual environment (if you have one)
source venv/bin/activate  # or source env/bin/activate

# Install/update packages
pip install -r requirements.txt

# Specifically ensure these are installed
pip install python-dotenv PyPDF2
```

---

## 🎨 Step 9: Collect Static Files

```bash
python3 manage.py collectstatic --noinput
```

---

## ✅ Step 10: Verify Configuration

```bash
# Run the configuration checker
python3 check_config.py
```

**Look for:**
- ✅ All green checkmarks
- ❌ Fix any red X marks before proceeding

---

## 🔄 Step 11: Restart Web Server

### For Apache:
```bash
sudo systemctl restart apache2
sudo systemctl status apache2
```

### For Nginx + Gunicorn:
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

## 🧪 Step 12: Test the Fix

1. **Open your browser**
2. **Go to:** `https://fastcopies.in`
3. **Try to login**

### ✅ If it works:
Congratulations! The 500 error is fixed! 🎉

### ❌ If it still shows 500 error:

**Enable DEBUG temporarily to see the exact error:**

```bash
# Edit .env
nano .env

# Change DEBUG to True
DEBUG=True

# Save and restart
sudo systemctl restart apache2  # or gunicorn

# Try login again - you'll see the detailed error
# Then set DEBUG=False again!
```

---

## 📊 Step 13: Check Error Logs

If still having issues, check the logs:

```bash
# Apache logs
tail -f /var/log/apache2/error.log

# Nginx logs
tail -f /var/log/nginx/error.log

# Gunicorn logs
journalctl -u gunicorn -f

# Django logs (if configured)
tail -f /var/www/fastcopy/logs/django.log
```

---

## 🔒 Step 14: Security Check (IMPORTANT!)

After everything works:

```bash
# Edit .env
nano .env

# Make sure these are set correctly:
DEBUG=False
SECRET_KEY=<your-unique-secret-key-not-the-default>

# Save and restart
sudo systemctl restart apache2  # or gunicorn
```

---

## 📋 Quick Command Summary

Copy-paste these commands in order:

```bash
# 1. SSH and navigate
ssh root@64.227.174.109
cd /var/www/fastcopy

# 2. Pull latest code
git pull origin main

# 3. Run diagnostic
bash fix_server.sh

# 4. Edit .env (fill with actual values!)
nano .env

# 5. Setup database and directories
python3 manage.py migrate
mkdir -p media staticfiles temp
chmod 664 fast_copy_duplic_db.sqlite3
chmod 775 . media staticfiles temp

# 6. Install dependencies
pip install -r requirements.txt

# 7. Collect static files
python3 manage.py collectstatic --noinput

# 8. Verify config
python3 check_config.py

# 9. Restart server
sudo systemctl restart apache2  # or gunicorn + nginx

# 10. Test in browser
# Go to: https://fastcopies.in/login/
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| `git pull` fails | Run `git stash` first, then `git pull` |
| Permission denied | Add `sudo` before the command |
| Database locked | Stop web server first: `sudo systemctl stop apache2` |
| Module not found | Run `pip install -r requirements.txt` |
| Still 500 error | Check logs: `tail -f /var/log/apache2/error.log` |

---

## ✅ Final Verification Checklist

- [ ] Code pulled from Git successfully
- [ ] `.env` file created with actual credentials
- [ ] `SECRET_KEY` is unique (not the default)
- [ ] `DEBUG=False` in production
- [ ] Database file exists with correct permissions
- [ ] All directories created (media, staticfiles, temp)
- [ ] Dependencies installed
- [ ] Static files collected
- [ ] `check_config.py` shows all green ✅
- [ ] Web server restarted
- [ ] Can access homepage
- [ ] **Can login without 500 error** ✨

---

## 📞 Need Help?

If you encounter any issues:

1. Run `python3 check_config.py > diagnostic.txt`
2. Check error logs: `tail -100 /var/log/apache2/error.log > error.txt`
3. Share both files for specific help

Good luck! 🚀
