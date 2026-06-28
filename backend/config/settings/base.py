from pathlib import Path

import environ

from config.feedback_integrations import load_feedback_integration_settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 15),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    MAX_FAILED_LOGIN_ATTEMPTS=(int, 5),
    ACCOUNT_LOCKOUT_MINUTES=(int, 30),
    PASSWORD_RESET_TOKEN_HOURS=(int, 1),
    ADMISSION_MAX_DOCUMENT_SIZE_MB=(int, 10),
    ADMISSION_PRESIGNED_URL_EXPIRY_SECONDS=(int, 3600),
    ADMISSION_APPLICATION_FEE=(float, 500.0),
    PUBLIC_API_BASE_URL=(str, "http://localhost:8000"),
    PUBLIC_APP_BASE_URL=(str, "http://localhost:3000/apply"),
    MEDIA_MAX_FILE_SIZE_MB=(int, 50),
    MEDIA_PRESIGNED_URL_EXPIRY_SECONDS=(int, 3600),
    PRACTICE_MAX_AUDIO_MB=(int, 25),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-in-production")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "apps.core",
    "apps.accounts",
    "apps.rbac",
    "apps.branches",
    "apps.audit",
    "apps.admissions",
    "apps.academics",
    "apps.students",
    "apps.scheduling",
    "apps.curriculum",
    "apps.learning",
    "apps.certifications",
    "apps.donations",
    "apps.hostel",
    "apps.notifications",
    "apps.community",
    "apps.chant_evaluator",
    "apps.alumni",
    "apps.feedback",
    "apps.gurukulam_feedback",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.audit.middleware.AuditContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.accounts.validators.PasswordComplexityValidator"},
]

AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.BranchJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("JWT_REFRESH_TOKEN_LIFETIME_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.CustomTokenObtainPairSerializer",
}

MAX_FAILED_LOGIN_ATTEMPTS = env("MAX_FAILED_LOGIN_ATTEMPTS")
ACCOUNT_LOCKOUT_MINUTES = env("ACCOUNT_LOCKOUT_MINUTES")
PASSWORD_RESET_TOKEN_HOURS = env("PASSWORD_RESET_TOKEN_HOURS")

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "x-branch-id",
    "x-device-fingerprint",
    "x-requested-with",
]

BRANCH_HEADER = "HTTP_X_BRANCH_ID"

AUDITED_MODELS = [
    "accounts.user",
    "accounts.userprofile",
    "rbac.role",
    "rbac.permission",
    "rbac.rolepermission",
    "rbac.userroleassignment",
    "branches.branch",
    "branches.userbranchmembership",
    "admissions.admissionapplication",
    "admissions.applicationdocument",
]

SENSITIVE_AUDIT_FIELDS = {
    "password",
    "password_hash",
    "token_hash",
    "token",
    "refresh",
    "access",
    "access_token",
    "gateway_signature",
}

# Admissions / S3 / Payments
ADMISSION_MAX_DOCUMENT_SIZE_MB = env("ADMISSION_MAX_DOCUMENT_SIZE_MB")
ADMISSION_PRESIGNED_URL_EXPIRY_SECONDS = env("ADMISSION_PRESIGNED_URL_EXPIRY_SECONDS")
ADMISSION_APPLICATION_FEE = env("ADMISSION_APPLICATION_FEE")
PUBLIC_API_BASE_URL = env("PUBLIC_API_BASE_URL")
PUBLIC_APP_BASE_URL = env("PUBLIC_APP_BASE_URL")
MEDIA_MAX_FILE_SIZE_MB = env("MEDIA_MAX_FILE_SIZE_MB")
MEDIA_PRESIGNED_URL_EXPIRY_SECONDS = env("MEDIA_PRESIGNED_URL_EXPIRY_SECONDS")
PRACTICE_MAX_AUDIO_MB = env("PRACTICE_MAX_AUDIO_MB")

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="ap-south-1")

RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET", default="")

ORGANIZATION_LEGAL_NAME = env("ORGANIZATION_LEGAL_NAME", default="Digital Veda Gurukulam Trust")
DONATION_12A_REGISTRATION = env("DONATION_12A_REGISTRATION", default="12A/XXXX/XXXX")
DONATION_80G_REGISTRATION = env("DONATION_80G_REGISTRATION", default="80G/XXXX/XXXX")

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="admissions@gurukulam.local")
WHATSAPP_ENABLED = env.bool("WHATSAPP_ENABLED", default=False)
WHATSAPP_API_URL = env("WHATSAPP_API_URL", default="")
WHATSAPP_API_TOKEN = env("WHATSAPP_API_TOKEN", default="")
SMS_ENABLED = env.bool("SMS_ENABLED", default=False)
SMS_API_URL = env("SMS_API_URL", default="")
SMS_API_TOKEN = env("SMS_API_TOKEN", default="")
DATA_CONSENT_VERSION = env("DATA_CONSENT_VERSION", default="v1.0")

CHANT_STT_ENABLED = env.bool("CHANT_STT_ENABLED", default=False)
CHANT_STT_API_URL = env("CHANT_STT_API_URL", default="")
CHANT_STT_API_TOKEN = env("CHANT_STT_API_TOKEN", default="")

# Feedback & issue-management integrations (see backend/.env.example)
FEEDBACK_INTEGRATIONS = load_feedback_integration_settings(env)
FEEDBACK_DEFAULT_ENV = FEEDBACK_INTEGRATIONS["general"]["default_env"]
FEEDBACK_ISSUE_TRACKER = FEEDBACK_INTEGRATIONS["general"]["issue_tracker"]
FEEDBACK_AUTO_CREATE_ISSUE = FEEDBACK_INTEGRATIONS["general"]["auto_create_issue"]
FEEDBACK_AUTO_GITHUB = FEEDBACK_AUTO_CREATE_ISSUE  # backward compatible alias

_GITHUB = FEEDBACK_INTEGRATIONS["github"]
GITHUB_ENABLED = _GITHUB["enabled"]
GITHUB_TOKEN = _GITHUB["token"]
GITHUB_REPO = _GITHUB["repo"]
GITHUB_API_URL = _GITHUB["api_url"]
GITHUB_LABELS = _GITHUB["labels"]
GITHUB_MILESTONE = _GITHUB["milestone"]
GITHUB_PROJECT_NODE_ID = _GITHUB["project_node_id"]
GITHUB_DEFAULT_BRANCH = _GITHUB["default_branch"]
GITHUB_BRANCH_PREFIX = _GITHUB["branch_prefix"]
GITHUB_AUTO_CREATE_BRANCH = _GITHUB["auto_create_branch"]

_GITLAB = FEEDBACK_INTEGRATIONS["gitlab"]
GITLAB_ENABLED = _GITLAB["enabled"]
GITLAB_TOKEN = _GITLAB["token"]
GITLAB_PROJECT_ID = _GITLAB["project_id"]
GITLAB_API_URL = _GITLAB["api_url"]

_JIRA = FEEDBACK_INTEGRATIONS["jira"]
JIRA_ENABLED = _JIRA["enabled"]
JIRA_BASE_URL = _JIRA["base_url"]
JIRA_EMAIL = _JIRA["email"]
JIRA_API_TOKEN = _JIRA["api_token"]
JIRA_PROJECT_KEY = _JIRA["project_key"]

_AZURE = FEEDBACK_INTEGRATIONS["azure_boards"]
AZURE_BOARDS_ENABLED = _AZURE["enabled"]
AZURE_DEVOPS_ORG = _AZURE["organization"]
AZURE_DEVOPS_PROJECT = _AZURE["project"]
AZURE_DEVOPS_PAT = _AZURE["pat"]
AZURE_BOARDS_WORK_ITEM_TYPE = _AZURE["work_item_type"]
AZURE_DEVOPS_API_URL = _AZURE["api_url"]

_SLACK = FEEDBACK_INTEGRATIONS["slack"]
SLACK_ENABLED = _SLACK["enabled"]
SLACK_BOT_TOKEN = _SLACK["bot_token"]
SLACK_WEBHOOK_URL = _SLACK["webhook_url"]
SLACK_CHANNEL = _SLACK["channel"]
SLACK_NOTIFY_ON_SUBMIT = _SLACK["notify_on_submit"]
SLACK_NOTIFY_ON_ISSUE_CREATED = _SLACK["notify_on_issue_created"]
