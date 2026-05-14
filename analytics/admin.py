"""
Резервное копирование БД из админки (нижний блок на главной странице админки).
Аналитика: /analytics/dashboard/
"""
import os
import subprocess
import tempfile

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone

from users.roles import is_manager


class AdminDatabaseBackupMixin:
    """POST /admin/backup-database/ — скачивание дампа PostgreSQL (pg_dump)."""

    def get_urls(self):
        custom = [
            path(
                "backup-database/",
                self.admin_view(self.backup_database_view),
                name="backup_database",
            ),
        ]
        return custom + super().get_urls()

    def backup_database_view(self, request):
        if not is_manager(request.user):
            raise PermissionDenied

        if request.method != "POST":
            return redirect("admin:index")

        db = settings.DATABASES.get("default", {})
        db_engine = db.get("ENGINE", "")
        if "postgresql" not in db_engine:
            messages.error(request, "Бэкап кнопкой поддерживается только для PostgreSQL.")
            return redirect("admin:index")

        db_name = db.get("NAME")
        db_user = db.get("USER")
        db_password = db.get("PASSWORD", "")
        db_host = db.get("HOST") or "localhost"
        db_port = str(db.get("PORT") or "5432")
        if not db_name or not db_user:
            messages.error(request, "В настройках БД не заполнены NAME/USER.")
            return redirect("admin:index")

        filename = f"db_backup_{db_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as tmp_file:
            tmp_path = tmp_file.name

        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        cmd = [
            "pg_dump",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "-F",
            "p",
            "-f",
            tmp_path,
        ]
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                err = (result.stderr or "").strip() or "Неизвестная ошибка pg_dump."
                messages.error(request, f"Не удалось создать бэкап: {err}")
                return redirect("admin:index")

            with open(tmp_path, "rb") as f:
                sql_data = f.read()

            response = HttpResponse(sql_data, content_type="application/sql; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except FileNotFoundError:
            messages.error(
                request,
                "Утилита pg_dump не найдена. Установите PostgreSQL client tools и перезапустите сервер.",
            )
            return redirect("admin:index")
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


admin.site.__class__ = type(
    "AdminSiteWithBackup",
    (AdminDatabaseBackupMixin, admin.site.__class__),
    {},
)
admin.site.index_template = "admin_overrides/index.html"
