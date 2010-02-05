# Django local settings for edc project.

# all settings in debug section should be false in production environment
[debug]
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEV_ENV = True

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

#We will not be using a RDB but this will allow tests to run
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'no_db'

#Specify Session Engine
CACHE_BACKEND = 'file:///tmp/django_cache'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

#Exist DB Settings
EXISTDB_SERVER_PROTOCOL = "http://"
# hostname, port, & path to exist xmlrpc - e.g., "localhost:8080/exist/xmlrpc"
EXISTDB_SERVER_HOST     = ""
EXISTDB_SERVER_USER     = ""
EXISTDB_SERVER_PWD      = ""
EXISTDB_SERVER_URL      = EXISTDB_SERVER_PROTOCOL + EXISTDB_SERVER_USER + ":" + \
    EXISTDB_SERVER_PWD + "@" + EXISTDB_SERVER_HOST
# collection should begin with / -  e.g., /edc
EXISTDB_ROOT_COLLECTION = ""
EXISTDB_TEST_COLLECTION = ""

ADDITIONAL_DATA_INDEX   = ""
DOI_PURL_HOST = "http://dx.doi.org/"

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
USE_I18N = True

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
SECRET_KEY = ''