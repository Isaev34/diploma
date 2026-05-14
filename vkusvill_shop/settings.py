"""
Django settings for vkusvill_shop project.
"""
import os
import dj_database_url
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Безопасность ────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-0(i31k)4_x#n!s+u=-qjc1f1keg91_luoz07j7_hky1^e1vtdt")

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

CSRF_TRUSTED_ORIGINS = [
    'https://*.trycloudflare.com',
    'https://tunnel4.com',
    'https://*.tuna.am',
    'https://*.onrender.com',  # ← добавлено для Render
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # ← для Render HTTPS

# ─── Приложения ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    # Local
    "users",
    "catalog",
    "cart",
    "api",
    "analytics",
    "shifts",
    "support",
]

JAZZMIN_SETTINGS = {
    "site_title": "LogiDrive Administration",
    "site_header": "LogiDrive Administration",
    "site_brand": "LogiDrive Administration",
    "welcome_sign": "Панель управления заказами",
    "show_ui_builder": True,
    "navigation_expanded": True,
    "topmenu_links": [
        {"name": "Главная", "url": "admin:index"},
        {"name": "Аналитика", "url": "/analytics/dashboard/", "new_window": True},
    ],
    "custom_links": {
        "catalog": [
            {
                "name": "Аналитика",
                "url": "/analytics/dashboard/",
                "icon": "fas fa-chart-line",
                "new_window": True,
            }
        ]
    },
    "icons": {
        "cart": "fas fa-shopping-cart",
        "users": "fas fa-users",
        "catalog": "fas fa-box-open",
    },
}

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ← добавлено (статика без Nginx)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "users.middleware.UserActivityLoggingMiddleware",
]

ROOT_URLCONF = "vkusvill_shop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "catalog.context_processors.nav_categories",
                "catalog.context_processors.favourite_ids",
            ],
        },
    },
]

WSGI_APPLICATION = "vkusvill_shop.wsgi.application"

# ─── База данных ─────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Render: переменная DATABASE_URL подставляется автоматически
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Локальная разработка
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "vkusvill_shop",
            "USER": "postgres",
            "PASSWORD": "isaev",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }

# ─── Валидация паролей ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Интернационализация ──────────────────────────────────────────────────────
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# ─── Статика ─────────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # ← добавлено для collectstatic
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # ← WhiteNoise

# ─── Медиафайлы ──────────────────────────────────────────────────────────────
# ⚠️ На Render файлы не сохраняются между деплоями.
# Для production подключи Cloudinary (см. DEPLOY_GUIDE.md).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Прочее ──────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"
LOGIN_URL = "/users/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

ADMIN_SITE_HEADER = "Администрирование"
ADMIN_SITE_TITLE = "Интернет-магазин"
ADMIN_INDEX_TITLE = "Панель управления"

# ─── API ключи (читаем из env, локально берём хардкод) ──────────────────────
YANDEX_MAPS_API_KEY = os.environ.get("YANDEX_MAPS_API_KEY", "51b1e94e-fc6d-4644-8583-e7f47a1c0300")
DADATA_API_KEY = os.environ.get("DADATA_API_KEY", "5c0ce4da68cb1803412112c7a4f78ba35e8abced")
DADATA_SECRET_KEY = os.environ.get("DADATA_SECRET_KEY", "7d85481fd8fcc99e85c1f1ff0efda41c2babd1de")

# ─── REST Framework ──────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'REST API',
    'DESCRIPTION': 'REST API для интернет-магазина продуктов',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
}

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "dostavka.info.logi@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "cvpo qxgw ierl uhty")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER