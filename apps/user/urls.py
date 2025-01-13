from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from chealth.middleware import login_not_required

from . import views
from .forms import CustomPasswordChangeForm

urlpatterns = [
    path('signup/', login_not_required(views.signup), name='signup'),
    path('account-activation-sent/', login_not_required(views.account_activation_sent),
         name='account_activation_sent'),
    path('account-activation-invalid/', login_not_required(views.account_activation_invalid),
         name='account_activation_invalid'),
    path('account-activation-done/', login_not_required(TemplateView.as_view(
        template_name='user/account_activation_done.html', extra_context={'no_sidebar': True})),
         name='account_activation_done'),
    path('resend-activation-email/', login_not_required(views.resend_activation_email),
         name='resend_activation_email'),
    path('activate/<uidb64>/<token>/', login_not_required(views.activate), name='activate'),
    path('login/', login_not_required(views.Login.as_view()), name='login'),
    path('logout/', login_not_required(auth_views.LogoutView.as_view(template_name='user/logout.html')), name='logout'),
    path('a/logout/', login_not_required(views.ajax_logout), name='ajax_logout'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='user/password_change.html', form_class=CustomPasswordChangeForm),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='user/password_change_done.html'),
         name='password_change_done'),
    path('password-reset/', login_not_required(auth_views.PasswordResetView.as_view(
         template_name='user/password_reset.html', email_template_name='user/password_reset_email.html',
         subject_template_name='user/password_reset_subject.txt', extra_context={'no_sidebar': True})),
         name='password_reset'),
    path('password-reset/done/', login_not_required(auth_views.PasswordResetDoneView.as_view(
         template_name='user/password_reset_done.html', extra_context={'no_sidebar': True})),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', login_not_required(auth_views.PasswordResetConfirmView.as_view(
         template_name='user/password_reset_confirm.html', extra_context={'no_sidebar': True})),
         name='password_reset_confirm'),
    path('reset/done/', login_not_required(auth_views.PasswordResetCompleteView.as_view(
        template_name='user/password_reset_complete.html', extra_context={'no_sidebar': True})),
         name='password_reset_complete'),
    path('auth/', login_not_required(views.Auth.as_view()), name='auth'),
    path('auth/error/', login_not_required(views.auth_error), name='auth_error'),
    path('auth/a/r/', login_not_required(views.auth_react), name='auth_react'),
    path('auth/p/r/', login_not_required(views.AuthPasswordResetView.as_view()), name='auth_password_reset'),
    path('auth/iu/', login_not_required(views.auth_inactive_user), name='auth_inactive'),
    path('auth/iu/r', login_not_required(views.auth_account_reset), name='auth_account_reset'),
    path('lockout/', login_not_required(views.lockout), name='lockout'),
    # User profile
    path('profile/', views.profile, {'template_name': 'user/profile.html'}, name='profile'),
    path('account/', views.profile, {'template_name': 'user/account.html'}, name='account'),
    path('image/upload/', views.upload_image, name='upload_image'),
    path('image/delete/', views.delete_image, name='delete_image'),
    path('p/s/', views.set_password, name='set_pw'),
    path('p/s/d/', login_not_required(views.set_password_done), name='set_pw_done'),
    path('p/s/r/', login_not_required(views.set_password_reactivation), name='set_pw_react')
]
