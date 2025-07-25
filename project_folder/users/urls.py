from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login', views.CustomLoginView.as_view(), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('register', views.registerUserView, name='register'),
    path('enable-mfa', views.enableMFAView, name='enable_mfa'),
    path('request-otp/<str:method>', views.requestOTPView, name='request_otp'),
    path('request-mfa/<str:modal>', views.requestMFAModalView, name='request_mfa'),
    path('profile/<int:user_id>', views.profileView, name='profile'),

    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset.html'),
        name='password_reset'),

    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'),
        name='password_reset_confirm'),

    path('password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'),
        name='password_reset_complete'),

    path('delete-this-user/<str:delete>', views.deleteUserView, name='delete_this_user'),
]