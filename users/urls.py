from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import BootstrapPasswordResetForm, BootstrapSetPasswordForm

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('signup/done/', views.signup_done_view, name='signup_done'),
    path(
        'activate/<uidb64>/<token>/',
        views.activate_view,
        name='activate',
    ),
    path(
        'resend-verification/',
        views.resend_verification_view,
        name='resend_verification',
    ),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            form_class=BootstrapPasswordResetForm,
            email_template_name='users/email/password_reset_body.txt',
            subject_template_name='users/email/password_reset_subject.txt',
            success_url=reverse_lazy('users:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            form_class=BootstrapSetPasswordForm,
            success_url=reverse_lazy('users:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('cards/', views.cards_view, name='cards'),
    path('cards/add/', views.add_card_view, name='add_card'),
    path('cards/<int:card_id>/delete/', views.delete_card_view, name='delete_card'),
    path('cards/<int:card_id>/set-default/', views.set_default_card_view, name='set_default_card'),
    path('addresses/', views.addresses_view, name='addresses'),
    path('addresses/add/', views.add_address_view, name='add_address'),
    path('addresses/<int:address_id>/delete/', views.delete_address_view, name='delete_address'),
    path('addresses/<int:address_id>/set-default/', views.set_default_address_view, name='set_default_address'),
]

