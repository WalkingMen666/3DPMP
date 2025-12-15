from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to use frontend URLs for email verification and password reset."""

    def send_mail(self, template_prefix, email, context):
        """Override to use frontend URL for email confirmation and password reset."""
        # Handle email verification
        if 'key' in context:
            context['activate_url'] = f"{settings.FRONTEND_URL}/verify-email/{context['key']}"

        # Handle password reset
        if 'password_reset_url' in context:
            # Extract uid and token from the original URL if present
            # The context might have uid and token separately, or in the password_reset_url
            uid = context.get('uid', '')
            token = context.get('token', '')
            if uid and token:
                context['password_reset_url'] = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}"

        return super().send_mail(template_prefix, email, context)
