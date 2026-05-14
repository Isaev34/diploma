from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_verification_token


def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    path = reverse("users:activate", kwargs={"uidb64": uid, "token": token})
    link = request.build_absolute_uri(path)
    ctx = {"user": user, "link": link}
    subject = "Подтверждение регистрации — LogiDrive"
    body = render_to_string("users/email/verification_body.txt", ctx).strip()
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
