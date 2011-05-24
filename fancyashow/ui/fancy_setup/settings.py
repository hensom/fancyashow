DEBUG          = False
DEBUG_SQL      = False

DATABASE_ENGINE   = 'dummy' # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME     = ''       # Or path to database file if using sqlite3.
DATABASE_USER     = ''       # Not used with sqlite3.
DATABASE_PASSWORD = ''       # Not used with sqlite3.
DATABASE_HOST     = ''       # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT     = ''

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '$w4kg3+b1nm69bya+un7si^3e)c_e410+ua82!pta(s@-8^730'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = (
  'fancyashow.ui.fancy_main.auth.FacebookBackend',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'fancyashow.ui.fancy_main.context_processors.site_info',
    'fancyashow.ui.fancy_main.context_processors.analytics',
)

ROOT_URLCONF = 'fancyashow.ui.fancy_setup.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

DATE_FORMAT = 'M d, Y'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.humanize',
    'password_required',
    'fancyashow.ui.fancy_setup',
    'fancyashow.ui.fancy_main',
    'fancyashow.ui.fancy_api',
    'fancyashow.ui.fancy_admin',
)

GOOGLE_ANALYTICS_ACCOUNT = None
PARSE_STAT_MAX_HISTORY   = 5

RESOURCE_VERSION = 6
STATIC_BASE_URL  = '/static'

import sys
import logging

LOG_ENABLED  = True
LOG_LEVEL    = logging.DEBUG
LOG_FORMAT   = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE     = sys.stderr

SITE_NAME    = 'Fancy a Show: '
SITE_TAGLINE = 'Live Music Shows in NYC'
DEFAULT_LOCATION_NAME = 'NYC'
