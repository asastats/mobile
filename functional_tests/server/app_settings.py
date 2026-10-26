"""frontend's development settings, reachable from the Android emulator (10.0.2.2)."""

from config.settings.development import *  # noqa: F401,F403

ALLOWED_HOSTS = ["10.0.2.2", "127.0.0.1", "localhost"]
CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, "http://10.0.2.2:8000"]  # noqa: F405
