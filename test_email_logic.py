
import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fastCopyConfig.settings')
django.setup()

def test_email():
    print("--- 📧 Testing Email Configuration ---")
    print(f"DEBUG Mode: {settings.DEBUG}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    
    # Mask password for safety
    pwd = settings.EMAIL_HOST_PASSWORD
    masked_pwd = f"{pwd[:2]}...{pwd[-2:]}" if pwd else "None"
    print(f"EMAIL_HOST_PASSWORD: {masked_pwd}")

    recipient = settings.ADMIN_EMAIL
    print(f"\nAttempting to send test email to: {recipient}")

    try:
        send_mail(
            subject='FastCopy Server Email Test',
            message='This is a test email from your FastCopy server. If you see this, email is working!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print("\n✅ SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"\n❌ FAILED: Error sending email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email()
