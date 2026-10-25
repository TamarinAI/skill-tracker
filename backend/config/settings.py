"""Django settings for the Monash Automation skill tracker.

Standalone service split out of discordbot. Auth is a shared bearer token
(SKILL_TRACKER_TOKEN) for bot/server-to-server calls; admin actions require
the caller Member to carry is_admin=True.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "skills",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "skills.middleware.ApiTokenMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SKILL_TRACKER_DB", str(BASE_DIR / "db.sqlite3")),
    }
}

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# Shared secret for API calls (discordbot / Tamarin / training site backend).
# Env var wins; otherwise read from SKILL_TRACKER_TOKEN_FILE (default .token
# next to the db) so local dev doesn't put secrets in shell history.
def _load_token() -> str:
    env = os.environ.get("SKILL_TRACKER_TOKEN", "")
    if env:
        return env
    token_file = Path(os.environ.get("SKILL_TRACKER_TOKEN_FILE", str(BASE_DIR / ".token")))
    try:
        return token_file.read_text().strip()
    except OSError:
        return ""


SKILL_TRACKER_TOKEN = _load_token()
