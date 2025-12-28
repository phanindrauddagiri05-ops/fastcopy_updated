import os
from pathlib import Path

# 1. BASE DIRECTORY 
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. SECURITY SETTINGS
SECRET_KEY = 'django-insecure-6zu4gfg3+vl-_*n8alvnmq#!kt-6+o9&r-w+$@0hzg76_50o9!'
DEBUG = True
ALLOWED_HOSTS = []

# --- 💳 CASHFREE PAYMENT GATEWAY CONFIG (Test Environment) ---
CASHFREE_APP_ID = "TEST1093498216f1366473dc23b3944128943901"
CASHFREE_SECRET_KEY = "cfsk_ma_test_0b9ab70120232dc4e71a533ea085249e_5d421d69"
CASHFREE_API_VERSION = "2023-08-01"
CASHFREE_API_URL = "https://sandbox.cashfree.com/pg"

# 3. APPLICATION DEFINITION
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core', # Your main app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fastCopyConfig.urls'

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
<<<<<<< HEAD
                'core.context_processors.cart_count',
                'core.context_processors.site_context', # Global site context (Holidays)
=======
                'core.context_processors.cart_count',  # Cart count globally available
>>>>>>> 87798d27c0daccfb5675ed1a1ab427eb83bcc2fc
            ],
        },
    },
]

WSGI_APPLICATION = 'fastCopyConfig.wsgi.application'

# 5. DATABASE (SQLite Configuration - For Testing)
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