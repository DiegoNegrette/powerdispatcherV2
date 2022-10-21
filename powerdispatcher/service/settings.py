import environ
from pathlib import Path

from service.logging import LOGGING  # noqa

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, True)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str(
    'DJANGO_SECRET_KEY',
    default='django-insecure-segr^u_$+(ai5rxc+vi8cmhn%1gd5mffbmke5c^7(ig!=je&k*'  # noqa
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'solo',
    # 'powerdispatcher.apps.PowerdispatcherConfig',
    'powerdispatcher'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DEBUG_TOOLBAR_ENABLED = env.bool('DEBUG_TOOLBAR_ENABLED', default=False)
if DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        # Toolbar options
        'RESULTS_CACHE_SIZE': 3,
        'SHOW_COLLAPSED': True,
        # Panel options
        'SQL_WARNING_THRESHOLD': 100,   # milliseconds
    }

ROOT_URLCONF = 'service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'service.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # noqa
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'US/Central'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# ------------ Celery
APP_VHOST = env.str('APP_VHOST', default='powerdispatch')
CELERY_BROKER_URL = env.str('CELERY_BROKER_URL', f'pyamqp://rabbitmq:rabbitmq@rabbitmq:5672/{APP_VHOST}')  # noqa
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ALWAYS_EAGER = env.bool('DJ_CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_IGNORE_RESULT = True
CELERY_DEFAULT_QUEUE = 'default'
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_ACKS_LATE = True

HEADLESS = env.bool('HEADLESS', default=True)
BROWSER = env.str('BROWSER', default='chrome')
CONNECTION_TYPE = env.str('CONNECTION_TYPE', default='remote')
WEB_DRIVER_URL = env.str('WEB_DRIVER_URL', default='')
WEB_DRIVER_PATH = env.str('WEB_DRIVER_PATH', default='/chromedriver')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
