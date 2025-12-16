from dj_rest_auth.forms import AllAuthPasswordResetForm
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from allauth.account.adapter import get_adapter
from allauth.account import app_settings as allauth_account_settings
from allauth.account.utils import user_username


class CustomPasswordResetForm(AllAuthPasswordResetForm):
    """Custom password reset form to use frontend URLs."""

    def save(self, request, **kwargs):
        """Override to use custom URL generator with frontend URL."""
        current_site = get_current_site(request)
        email = self.cleaned_data['email']
        token_generator = kwargs.get('token_generator', default_token_generator)

        for user in self.users:
            temp_key = token_generator.make_token(user)

            # Use UUID directly as string (no base64 encoding needed for UUID)
            uid = str(user.pk)

            # Create frontend URL directly
            url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{temp_key}"

            context = {
                'current_site': current_site,
                'user': user,
                'password_reset_url': url,
                'request': request,
            }
            if (
                allauth_account_settings.AUTHENTICATION_METHOD
                != allauth_account_settings.AuthenticationMethod.EMAIL
            ):
                context['username'] = user_username(user)

            # Send the email using allauth adapter
            get_adapter(request).send_mail(
                'account/email/password_reset_key', email, context
            )

        return self.cleaned_data['email']
