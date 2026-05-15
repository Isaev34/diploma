from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        try:
            from django.contrib.auth.models import Group
            from django.db.utils import OperationalError, ProgrammingError

            Group.objects.exists()
        except (OperationalError, ProgrammingError, ImportError):
            return
        from users.roles import ensure_role_groups
        ensure_role_groups(verbose=False)
