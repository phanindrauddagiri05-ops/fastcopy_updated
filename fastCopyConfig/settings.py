import os
from pathlib import Path

# 1. BASE DIRECTORY 
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. SECURITY SETTINGS
SECRET_KEY = 'django-insecure-6zu4gfg3+vl-_*n8alvnmq#!kt-6+o9&r-w+$@0hzg76_50o9!'
DEBUG = True
ALLOWED_HOSTS = []

# settings.py


# Standard Global Sandbox Credentials (Use these to fix the 400 error)
PHONEPE_MERCHANT_ID = "PGCHECKOUT"
PHONEPE_CLIENT_ID = "PGCHECKOUT"
PHONEPE_CLIENT_SECRET = "YzU1YTM4OGYtM2ZlOS00NDg1LWE2ZTYtZWMxNTdkOTdlZTUw"

# Keep these as they are
PHONEPE_AUTH_URL = "https://api-preprod.phonepe.com/apis/pg-sandbox/v1/oauth/token"
PHONEPE_PAY_URL = "https://api-preprod.phonepe.com/apis/pg-sandbox/v1/pay"

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
            ],
        },
    },
]

WSGI_APPLICATION = 'fastCopyConfig.wsgi.application'

# 5. DATABASE (MySQL Configuration)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fastCopyDatabase',
        'USER': 'root',
        'PASSWORD': 'PhaniUddagiri@2005',
        'HOST': 'localhost',
        'PORT': '3306',
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
# fastCopyConfig/settings.py

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
# When a student uploads a document, it will be saved in the /orders/ folder
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 10. DEFAULT AUTO FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'home'

# Optional: If you want to redirect them to home after logging out too
LOGOUT_REDIRECT_URL = 'home'

# --- 💳 PHONEPE GATEWAY CONFIG ---
PHONEPE_MERCHANT_ID = "PGMDATA" # Replace with your Merchant ID
PHONEPE_SALT_KEY = "YOUR_SALT_KEY" # Replace with your Salt Key
PHONEPE_SALT_INDEX = "1" # Usually '1'

# Sandbox URL for testing
PHONEPE_API_URL = "https://api-preprod.phonepe.com/apis/pg-sandbox/v1/pay"