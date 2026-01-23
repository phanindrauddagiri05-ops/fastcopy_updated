---
description: Complete step-by-step guide to deploy code to the server
---

# 🚀 FastCopy Server Deployment Guide

This workflow provides complete step-by-step commands to deploy your code to the server.

---

## Prerequisites

- Your server IP address or domain name
- SSH access credentials (username and password/key)
- Git repository is set up on the server

---

## Deployment Steps

### **Step 1: Connect to Your Server via SSH**

**Command:**
```bash
ssh root@194.163.173.57
```

**Description:**
- Establishes a secure connection to your server
- Replace `root` with your actual username if different
- Replace `194.163.173.57` with your server IP or domain
- You'll be prompted to enter your password

**How to run:**
1. Open your terminal (PowerShell, CMD, or Git Bash on Windows)
2. Type the command above
3. Press Enter
4. Enter your password when prompted (password will not be visible while typing)

---

### **Step 2: Navigate to Your Project Directory**

**Command:**
```bash
cd /var/www/fastcopy
```

**Description:**
- Changes directory to where your Django project is installed on the server
- Common locations might be `/home/username/fastcopy`, `/opt/fastcopy`, or `/var/www/fastcopy`
- Adjust the path based on where you initially deployed your project

**Verify you're in the right place:**
```bash
pwd
ls -la
```
- `pwd` shows your current directory path
- `ls -la` lists all files - you should see `manage.py`, `fastCopyConfig/`, `core/`, etc.

---

### **Step 3: Check Current Git Status**

**Command:**
```bash
git status
```

**Description:**
- Shows you which files have been modified on the server
- Tells you if you're behind the remote repository
- Helps identify any conflicts before pulling new code

**Expected output:**
- Should show "Your branch is up to date" or "Your branch is behind"
- May show modified files if you made changes on the server

---

### **Step 4: Stash Any Local Changes (If Needed)**

**Command:**
```bash
git stash
```

**Description:**
- Temporarily saves any uncommitted changes on the server
- Required if you made any edits directly on the server
- Prevents conflicts when pulling new code

**When to use:**
- Only run this if `git status` showed modified files
- Skip if status shows "nothing to commit, working tree clean"

---

### **Step 5: Pull Latest Code from Git Repository**

**Command:**
```bash
git pull origin main
```

**Description:**
- Downloads and merges the latest code changes from your Git repository
- `origin` is the name of your remote repository
- `main` is the branch name (could be `master` in older repositories)

**Expected output:**
```
Updating a1b2c3d..e4f5g6h
Fast-forward
 core/views.py              | 25 ++++++++++++++++++++-----
 templates/base.html        | 15 ++++++++-------
 3 files changed, 30 insertions(+), 12 deletions(-)
```

**If you get an error:**
- Make sure you ran `git stash` first if there were local changes
- Check your internet connection
- Verify your Git credentials are configured

---

### **Step 6: Activate Virtual Environment**

**Command:**
```bash
source venv/bin/activate
```

**Description:**
- Activates Python virtual environment where all your packages are installed
- Virtual environment keeps project dependencies isolated
- After activation, you'll see `(venv)` in your command prompt

**Alternative names:**
```bash
source env/bin/activate    # if your venv is named 'env'
source .venv/bin/activate  # if your venv is named '.venv'
```

**How to check which venv you have:**
```bash
ls -la | grep venv
```

---

### **Step 7: Install/Update Python Dependencies**

**Command:**
```bash
pip install -r requirements.txt
```

**Description:**
- Installs or updates all Python packages required by your project
- Reads from `requirements.txt` file
- Ensures all dependencies are at the correct versions

**What it installs:**
- Django
- MySQL client (mysqlclient or PyMySQL)
- python-dotenv (for .env files)
- Payment gateway libraries
- Any other packages your project needs

**Expected output:**
```
Requirement already satisfied: Django==4.2.7 in ./venv/lib/python3.10/site-packages
...
Successfully installed package-name-1.0.0
```

---

### **Step 8: Run Database Migrations**

**Command:**
```bash
python manage.py migrate
```

**Description:**
- Applies any new database schema changes
- Creates new tables, adds columns, or modifies existing database structure
- Safe to run multiple times - only applies pending migrations

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, core, sessions
Running migrations:
  Applying core.0015_new_field... OK
```

**If no changes:**
```
No migrations to apply.
```

---

### **Step 9: Collect Static Files**

**Command:**
```bash
python manage.py collectstatic --noinput
```

**Description:**
- Gathers all CSS, JavaScript, and image files into one location
- Web server (Nginx/Apache) serves these files directly
- `--noinput` flag automatically answers "yes" to overwrite prompts

**What it does:**
- Copies files from `static/` to `staticfiles/`
- Includes Django admin static files
- Optimizes for production serving

**Expected output:**
```
120 static files copied to '/var/www/fastcopy/staticfiles'.
```

---

### **Step 10: Check for Configuration Issues**

**Command:**
```bash
python check_config.py
```

**Description:**
- Runs custom diagnostic script (if available in your project)
- Verifies `.env` file settings
- Checks database connectivity
- Validates directory permissions

**What it checks:**
- ✅ .env file exists with required variables
- ✅ Database connection works
- ✅ Required directories exist (media, staticfiles)
- ✅ File permissions are correct

---

### **Step 11: Restart Gunicorn Service**

**Command:**
```bash
sudo systemctl restart gunicorn
```

**Description:**
- Restarts the Gunicorn application server
- Loads your new code into memory
- Gunicorn serves your Django application

**What Gunicorn does:**
- Runs your Django application
- Handles Python code execution
- Communicates with Nginx web server

**Check status:**
```bash
sudo systemctl status gunicorn
```

**Expected output:**
```
● gunicorn.service - gunicorn daemon
   Active: active (running) since Thu 2026-01-23 23:15:00 IST
```

---

### **Step 12: Restart Nginx Web Server**

**Command:**
```bash
sudo systemctl restart nginx
```

**Description:**
- Restarts the Nginx web server
- Applies any configuration changes
- Nginx serves static files and proxies requests to Gunicorn

**What Nginx does:**
- Serves static files (CSS, JS, images) directly
- Handles SSL/HTTPS certificates
- Forwards dynamic requests to Gunicorn

**Check status:**
```bash
sudo systemctl status nginx
```

**Expected output:**
```
● nginx.service - A high performance web server
   Active: active (running) since Thu 2026-01-23 23:15:05 IST
```

---

### **Step 13: Verify Services Are Running**

**Commands:**
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

**Description:**
- Checks if both services started successfully
- Shows any error messages if something went wrong
- Confirms services are "active (running)"

**Look for:**
- Green "active (running)" status
- No red error messages
- Process IDs (PIDs) indicating services are running

---

### **Step 14: Check Error Logs (If Issues Occur)**

**Commands:**
```bash
# Check Nginx error log
sudo tail -50 /var/log/nginx/error.log

# Check Gunicorn logs
sudo journalctl -u gunicorn -n 50

# Check application logs (if configured)
tail -50 /var/www/fastcopy/logs/django.log
```

**Description:**
- Views recent error messages from various services
- `-50` or `-n 50` shows last 50 lines
- `tail -f` follows logs in real-time (useful for debugging)

**When to use:**
- If website shows 500 or 502 error
- If services fail to start
- To debug any unexpected behavior

---

### **Step 15: Test Your Website**

**Action:**
1. Open your web browser
2. Go to your website URL: `https://aishwaryaxerox.in` or `https://fastcopy.pagexplore.com`
3. Test key functionality:
   - Homepage loads correctly
   - Can login
   - Can upload files
   - Can place orders
   - Payment gateway works

**If something doesn't work:**
- Check error logs (Step 14)
- Verify `.env` file has correct values
- Ensure static files were collected
- Check file permissions

---

### **Step 16: Clear Browser Cache (If UI Looks Old)**

**Command (server-side):**
```bash
# Add cache-busting parameter or clear old static files
python manage.py collectstatic --clear --noinput
```

**User-side:**
- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac) to hard refresh
- Or clear browser cache in settings

**Description:**
- Ensures users see the latest CSS/JavaScript
- Clears old cached static files
- Forces browser to download new versions

---

## 🔍 Additional Useful Commands

### Check Django Version
```bash
python manage.py --version
```

### Create Superuser (Admin Account)
```bash
python manage.py createsuperuser
```

### View All Running Services
```bash
sudo systemctl list-units --type=service --state=running
```

### Check Disk Space
```bash
df -h
```

### Check Server Resource Usage
```bash
htop
# Or: top
```

### Restart MySQL Database (if needed)
```bash
sudo systemctl restart mysql
sudo systemctl status mysql
```

---

## 📋 Quick Copy-Paste Commands (Complete Deployment)

Use this for quick deployments:

```bash
# 1. SSH into server
ssh root@194.163.173.57

# 2. Navigate to project
cd /var/www/fastcopy

# 3. Pull latest code
git stash
git pull origin main

# 4. Activate virtual environment
source venv/bin/activate

# 5. Update dependencies
pip install -r requirements.txt

# 6. Run migrations
python manage.py migrate

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# 9. Check status
sudo systemctl status gunicorn
sudo systemctl status nginx

# 10. Test website in browser
```

---

## 🆘 Troubleshooting Common Issues

### Issue: `git pull` fails with merge conflicts
**Solution:**
```bash
git stash
git pull origin main
```

### Issue: Permission denied errors
**Solution:**
```bash
# Add sudo before commands
sudo python manage.py migrate

# Or fix ownership
sudo chown -R $USER:$USER /var/www/fastcopy
```

### Issue: Module not found errors
**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: 502 Bad Gateway error
**Solution:**
```bash
# Check if Gunicorn is running
sudo systemctl status gunicorn

# Restart Gunicorn
sudo systemctl restart gunicorn

# Check Gunicorn logs
sudo journalctl -u gunicorn -n 50
```

### Issue: Static files not loading
**Solution:**
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput

# Check Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Issue: Database connection errors
**Solution:**
```bash
# Check MySQL is running
sudo systemctl status mysql

# Test database connection
python manage.py dbshell

# Check .env file has correct database credentials
cat .env | grep DATABASE
```

---

## ✅ Post-Deployment Checklist

After deployment, verify these items:

- [ ] Website loads without errors
- [ ] Can login to user account
- [ ] Can login to admin panel (`/admin`)
- [ ] File uploads work
- [ ] Payment gateway processes test payment
- [ ] Email notifications are sent
- [ ] All pages load correctly (About, Services, Contact, etc.)
- [ ] Mobile view looks correct
- [ ] SSL certificate is valid (https://)
- [ ] No console errors in browser (F12 → Console)

---

## 🔒 Security Reminders

After deployment, ensure:

1. **DEBUG is False in production**
   ```bash
   # Check .env file
   cat .env | grep DEBUG
   # Should show: DEBUG=False
   ```

2. **SECRET_KEY is unique and strong**
   ```bash
   # Generate new one if needed
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **ALLOWED_HOSTS is configured**
   ```bash
   # Check .env file
   cat .env | grep ALLOWED_HOSTS
   ```

4. **File permissions are correct**
   ```bash
   # Database file
   ls -la *.sqlite3
   # Should be: -rw-rw-r-- (664)
   
   # Media directory
   ls -ld media/
   # Should be: drwxrwxr-x (775)
   ```

---

## 📞 Support

If you encounter any issues during deployment:

1. Check the error logs (Step 14)
2. Review this guide for troubleshooting steps
3. Verify all services are running (Step 13)
4. Test each component individually

Good luck with your deployment! 🚀
