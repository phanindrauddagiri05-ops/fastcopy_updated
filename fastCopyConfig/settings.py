import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. BASE DIRECTORY 
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. SECURITY SETTINGS
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = [
    'https://fastcopies.in',
    'http://fastcopies.in',
    'https://www.fastcopies.in',
    'http://www.fastcopies.in',
    'https://194.163.173.57',
    'http://194.163.173.57'
]

# Production Security Settings (Critical for Reverse Proxy/SSL)
# Production Security Settings (Critical for Reverse Proxy/SSL)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'


# --- 💳 CASHFREE PAYMENT GATEWAY CONFIG (Production Environment) ---
CASHFREE_APP_ID = os.getenv('CASHFREE_APP_ID')
CASHFREE_SECRET_KEY = os.getenv('CASHFREE_SECRET_KEY')
CASHFREE_API_VERSION = os.getenv('CASHFREE_API_VERSION', '2023-08-01')
CASHFREE_API_URL = os.getenv('CASHFREE_API_URL', 'https://api.cashfree.com/pg')

# 3. APPLICATION DEFINITION
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',  # For dynamic sitemap generation
    'core', # Your main app
    
    # Allauth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.MaintenanceMiddleware', # Custom Maintenance Mode Middleware
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'fastCopyConfig.urls'

# 4. TEMPLATES (Configured to find your custom Admin & Core templates)
# 4. TEMPLATES (Configured to find your custom Admin & Core templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Custom Processors
                'core.context_processors.site_context', # Global site context (Holidays)
                'core.context_processors.cart_count',   # Cart count globally available
            ],
        },
    },
]

WSGI_APPLICATION = 'fastCopyConfig.wsgi.application'

# 5. DATABASE (MySQL Configuration)
# 5. DATABASE (SQLite by default, MySQL if configured)
if os.getenv('USE_MYSQL') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'fastcopy_database',
            'USER': 'root',
            'PASSWORD': 'PhaniUddagiri@2005',
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# 6. PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ALLAUTH CONFIGURATION
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# Reading the Keys from Environment Variables
SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
    'client_id': os.getenv('GOOGLE_CLIENT_ID'),
    'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
    'key': ''
}

LOGIN_REDIRECT_URL = 'home'
ACCOUNT_LOGOUT_REDIRECT_URL = 'login'
SOCIALACCOUNT_LOGIN_ON_GET = True # Optional: Skip confirm page if possible
ACCOUNT_LOGIN_METHODS = {'email'} # Replaces deprecated ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_SIGNUP_FIELDS = ['email', 'first_name', 'last_name'] # Explicitly define signup fields
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'


# 7. INTERNATIONALIZATION (India Specific)
LANGUAGE_CODE = 'en-us'

# Set this to Asia/Kolkata for correct India Time
TIME_ZONE = 'Asia/Kolkata' 

USE_I18N = True
USE_TZ = True # Keeps internal storage robust while displaying IST

# 8. STATIC FILES (CSS, JS, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 9. MEDIA FILES (For uploaded PDF/Image files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 10. DEFAULT AUTO FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# 11. EMAIL CONFIGURATION (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'fastcopyteam@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = f'FastCopy Team <{EMAIL_HOST_USER}>'

# 12. ADMIN & SUPPORT CONFIGURATION
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'fastcopyteam@gmail.com')
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'fastcopy003@gmail.com')
SUPPORT_PHONE = os.getenv('SUPPORT_PHONE', '+91 8500290959')
COMPANY_NAME = 'FastCopy'
COMPANY_WEBSITE = os.getenv('COMPANY_WEBSITE', 'http://localhost:8000')