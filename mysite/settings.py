"""
Django settings for mysite project.
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# --- Paths & .env ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # opcional para entorno local

# --- Seguridad / Debug -------------------------------------------------------
SECRET_KEY = 'django-insecure-rc^*w^w&6g9_(uvx#6s*bnt!w)l0rdi%!l7mv#y%uc&x%wo5pk'
DEBUG = True

# Incluye aquí tus dominios reales (Railway y producción)
ALLOWED_HOSTS = [
    "localhost", "127.0.0.1",
    "artesaniaspachy.cl",
    "server-production-e90b5.up.railway.app",  # cambia si tu subdominio es otro
]

# Evita el error de CSRF en admin/login y formularios
CSRF_TRUSTED_ORIGINS = [
    "https://artesaniaspachy.cl",
    "https://server-production-e90b5.up.railway.app",  # cambia si tu subdominio es otro
    # "https://*.railway.app",  # opcional
]

# --- Apps --------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Tus apps
    'cms',
    'core',        # Home público
    'catalog',     # CRUD interno
]

# Si existe CLOUDINARY_URL, activamos Cloudinary SOLO para MEDIA
if os.environ.get("CLOUDINARY_URL"):
    INSTALLED_APPS += ['cloudinary', 'cloudinary_storage']
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    # MEDIA_URL puede seguir siendo /media/; las ImageField devolverán URL absolutas de Cloudinary
else:
    # Media local (modo desarrollo sin Cloudinary)
    pass  # no cambiamos nada

# --- Media (valores por defecto; con Cloudinary no se usan en prod) ----------
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- Middleware --------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise justo después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',   # <--- AÑADE AQUÍ
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

# --- Templates ---------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # para base_site.html, home.html, etc.
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'core.context_processors.cart_badge',
                'core.context_processors.main_menu',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

# --- Base de Datos (Railway) -------------------------------------------------
DATABASE_URL = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("RAILWAY_DATABASE_URL")
    or os.environ.get("database_url")
)

if not DATABASE_URL:
    pg = {k: os.environ.get(k) for k in ["PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE"]}
    if all(pg.values()):
        DATABASE_URL = f"postgresql://{pg['PGUSER']}:{pg['PGPASSWORD']}@{pg['PGHOST']}:{pg['PGPORT']}/{pg['PGDATABASE']}"

if not DATABASE_URL:
    raise RuntimeError("No se encontró ninguna DATABASE_URL. Define DATABASE_URL en el servicio web de Railway.")

DATABASES = {"default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}

# --- Mercado Pago (env) ------------------------------------------------------
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
MP_PUBLIC_KEY   = os.getenv("MP_PUBLIC_KEY", "")
MP_WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET", "")  # opcional, para webhook

# --- Password validators -----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internacionalización (Chile) -------------------------------------------
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Idiomas disponibles
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

# Carpeta donde guardaremos los .po/.mo
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
LOCALE_PATHS = [BASE_DIR / 'locale']

# --- Static & WhiteNoise -----------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]      # carpeta de assets locales
STATIC_ROOT = BASE_DIR / "staticfiles"        # carpeta de recogida para prod (collectstatic)

# IMPORTANTE: mantenemos WhiteNoise con manifest para evitar el error del admin
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Proxy/HTTPS detrás de Railway ------------------------------------------
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- Login (para @login_required) -------------------------------------------
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/panel/productos/"

# --- Default PK --------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
