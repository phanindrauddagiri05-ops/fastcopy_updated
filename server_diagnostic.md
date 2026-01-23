# 🔧 FastCopy Server Error 500 - Diagnostic & Fix Guide

## ⚠️ Current Issue
- **Error**: Server Error (500) when logging in
- **URL**: `fastcopies.in/login/`
- **Symptom**: Site opens but login fails

---

## 🎯 Most Likely Causes (In Order of Probability)

### 1. **Missing or Incorrect `.env` File** (90% likely)
Your Django app loads environment variables from `.env` file. If this is missing on the server, authentication will fail.

**Required `.env` variables:**
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=fastcopies.in,www.fastcopies.in,64.227.174.109

# Email Configuration
EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Cashfree Payment Gateway
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_API_URL=https://api.cashfree.com/pg

# Company Details
ADMIN_EMAIL=fastcopyteam@gmail.com
SUPPORT_EMAIL=fastcopy003@gmail.com
SUPPORT_PHONE=+91 8500290959
COMPANY_WEBSITE=https://fastcopies.in
```

### 2. **Database File Missing or No Write Permissions** (80% likely)
SQLite database file `fast_copy_duplic_db.sqlite3` needs to exist and be writable.

### 3. **Missing Directories** (70% likely)
Required directories: `media/`, `staticfiles/`, `temp/`

### 4. **Python Dependencies Not Installed** (50% likely)
Missing packages like `python-dotenv`, `PyPDF2`, etc.

---

## 🚀 IMMEDIATE FIX - SSH Commands

Connect to your server and run these commands:

### Step 1: Navigate to Project Directory
```bash
cd /path/to/your/fastcopy/project
# Example: cd /var/www/fastcopy or cd /home/username/fastcopy
```

### Step 2: Check if .env File Exists
```bash
ls -la .env
```

**If missing, create it:**
```bash
nano .env
```
Then paste the environment variables from above and save (Ctrl+X, Y, Enter).

### Step 3: Check Database File
```bash
ls -la fast_copy_duplic_db.sqlite3
```

**If missing, create it:**
```bash
python manage.py migrate
```

### Step 4: Fix File Permissions
```bash
# Make sure web server can write to database
chmod 664 fast_copy_duplic_db.sqlite3
chmod 775 .

# Create and set permissions for required directories
mkdir -p media staticfiles temp
chmod 775 media staticfiles temp
```

### Step 5: Check Server Error Logs
```bash
# For Apache
tail -f /var/log/apache2/error.log

# For Nginx + Gunicorn
tail -f /var/log/nginx/error.log
journalctl -u gunicorn -f
```

### Step 6: Restart Web Server
```bash
# For Apache
sudo systemctl restart apache2

# For Nginx + Gunicorn
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 🔍 Enable DEBUG Mode Temporarily (To See Exact Error)

**⚠️ WARNING: Only do this temporarily to diagnose the issue!**

1. Edit your `.env` file on the server:
```bash
nano .env
```

2. Change this line:
```env
DEBUG=True
```

3. Restart the server:
```bash
sudo systemctl restart apache2  # or gunicorn
```

4. Try logging in again - you'll see the detailed error message
5. **IMPORTANT**: Set `DEBUG=False` again after fixing!

---

## 📋 Complete Server Deployment Checklist

Use this to verify everything is set up correctly:

- [ ] `.env` file exists with all required variables
- [ ] `SECRET_KEY` is set and different from the fallback
- [ ] Database file exists: `fast_copy_duplic_db.sqlite3`
- [ ] Database has write permissions (664)
- [ ] Project directory has write permissions (775)
- [ ] `media/` directory exists with 775 permissions
- [ ] `staticfiles/` directory exists with 775 permissions
- [ ] `temp/` directory exists with 775 permissions
- [ ] All Python dependencies installed: `pip install -r requirements.txt`
- [ ] Static files collected: `python manage.py collectstatic --noinput`
- [ ] Migrations applied: `python manage.py migrate`
- [ ] Web server restarted after changes

---

## 🔐 Security Notes

1. **Never commit `.env` to Git** - It contains sensitive credentials
2. **Use strong SECRET_KEY** - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
3. **Keep DEBUG=False in production**
4. **Use HTTPS** - Your domain should use SSL certificate

---

## 📞 If Still Not Working

Check the server error logs and look for:
- `ModuleNotFoundError` - Missing Python package
- `OperationalError` - Database issue
- `ImproperlyConfigured` - Settings problem
- `PermissionError` - File permission issue

Share the exact error from logs for specific help.
