# 🚨 FastCopy Server Error 500 - Quick Fix Guide

## 📋 **TL;DR - Run These Commands on Your Server**

```bash
# 1. SSH into your server
ssh username@64.227.174.109

# 2. Navigate to project directory (adjust path if different)
cd /var/www/fastcopy  # or wherever your project is

# 3. Run the diagnostic script
bash fix_server.sh

# 4. OR manually check configuration
python check_config.py

# 5. Edit .env file with actual credentials
nano .env

# 6. Restart web server
sudo systemctl restart apache2  # or gunicorn + nginx
```

---

## 🎯 **Most Common Fix (90% of cases)**

The `.env` file is missing or has wrong values. Create/edit it:

```bash
cd /var/www/fastcopy  # your project directory
nano .env
```

Paste this and **replace with your actual values**:

```env
SECRET_KEY=your-actual-secret-key-here
DEBUG=False
ALLOWED_HOSTS=fastcopy.pagexplore.com,64.227.174.109
EMAIL_HOST_USER=fastcopyteam@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
```

Save (Ctrl+X, Y, Enter) and restart:
```bash
sudo systemctl restart apache2  # or gunicorn
```

---

## 🔍 **How to See the Exact Error**

Temporarily enable DEBUG mode:

1. Edit `.env`:
   ```bash
   nano .env
   ```

2. Change to:
   ```env
   DEBUG=True
   ```

3. Restart server:
   ```bash
   sudo systemctl restart apache2
   ```

4. Try logging in - you'll see the detailed error

5. **IMPORTANT**: Set `DEBUG=False` again after fixing!

---

## 📊 **Error Log Locations**

Check these for detailed error messages:

```bash
# Apache
tail -f /var/log/apache2/error.log

# Nginx + Gunicorn
tail -f /var/log/nginx/error.log
journalctl -u gunicorn -f

# Django logs (if configured)
tail -f /var/www/fastcopy/logs/django.log
```

---

## ✅ **Verification Checklist**

After fixing, verify these:

- [ ] `.env` file exists with correct values
- [ ] Database file exists: `ls -la fast_copy_duplic_db.sqlite3`
- [ ] Directories exist: `media/`, `staticfiles/`, `temp/`
- [ ] Web server restarted
- [ ] Can access homepage: `https://fastcopy.pagexplore.com`
- [ ] Can login without 500 error

---

## 🆘 **Still Not Working?**

Run this to get full diagnostic info:

```bash
cd /var/www/fastcopy
python check_config.py > diagnostic_output.txt 2>&1
cat diagnostic_output.txt
```

Share the output for specific help.

---

## 📞 **Common Error Messages & Fixes**

| Error Message | Fix |
|---------------|-----|
| `ModuleNotFoundError: No module named 'dotenv'` | `pip install python-dotenv` |
| `OperationalError: unable to open database file` | Check database file exists and has write permissions |
| `ImproperlyConfigured: SECRET_KEY` | Set SECRET_KEY in .env file |
| `PermissionError: [Errno 13]` | Fix file permissions: `chmod 664 *.sqlite3` |

---

## 🔐 **Generate New SECRET_KEY**

If you need a new secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it in your `.env` file.
