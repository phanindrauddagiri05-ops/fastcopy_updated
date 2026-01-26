from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .utils import send_welcome_email

@receiver(user_signed_up)
def social_login_welcome_email(request, user, **kwargs):
    """
    Signal receiver to send welcome email when a user signs up via Social Account (Google).
    """
    print(f"Signal: User signed up via Social Account: {user.email}")
    send_welcome_email(user)
