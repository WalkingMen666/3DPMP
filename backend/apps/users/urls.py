from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('dj_rest_auth.urls')),
    path('registration/', include('dj_rest_auth.registration.urls')),
    path('me/', views.get_current_user, name='current-user'),
    path('profile/', views.update_profile, name='update-profile'),
    path('avatar/', views.update_avatar, name='update-avatar'),
    path('avatar/choices/', views.get_avatar_choices, name='avatar-choices'),
    # Google OAuth
    path('google/', views.google_login, name='google-login'),
    path('google/client-id/', views.google_client_id, name='google-client-id'),
]
