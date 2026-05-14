from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Токен подтверждения e-mail; после активации пользователя ссылка становится недействительной."""

    def _make_hash_value(self, user, timestamp):
        email = (user.email or "").strip().lower()
        return f"{user.pk}{timestamp}{user.is_active}{email}"


email_verification_token = EmailVerificationTokenGenerator()
