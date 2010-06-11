# Django local settings for finding aids project.

# all settings in debug section should be false in production environment
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEV_ENV = True

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# RDB used for user account management.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',   # The database backend you plan to use
        'NAME': 'database you are using',       # Database name
        'HOST': '',                             # Host you want to connect to. An empty string means localhost.
        'USER': 'user',                         # The username to use when connecting to the database.
        'PASSWORD': 'password',                 # The password to use when connecting to the database.
    }
}

#Specify Session Engine
CACHE_BACKEND = 'file:///tmp/django_cache'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

#Exist DB Settings
EXISTDB_SERVER_URL      = 'http://user:password@existdb.example.com/exist/xmlrpc'
# collection should begin with / -  e.g., /edc
EXISTDB_ROOT_COLLECTION = ""
# preview collection - should be outside main findingaids collection
EXISTDB_PREVIEW_COLLECTION = ""
EXISTDB_TEST_COLLECTION = ""

# EULCORE LDAP SETTINGS
# LDAP login settings. These are configured for emory, but you'll need
# to get a base user DN and password elsewhere.
AUTH_LDAP_SERVER = '' # i.e. 'ldaps://vlad.service.emory.edu'
AUTH_LDAP_BASE_USER = '' # i.e. 'uid=USERNAME,ou=services,o=emory.edu'
AUTH_LDAP_BASE_PASS = '' # password for USERNAME above
AUTH_LDAP_SEARCH_SUFFIX = '' # i.e. 'o=emory.edu'
AUTH_LDAP_SEARCH_FILTER = '' # i.e. '(uid=%s)'
AUTH_LDAP_CHECK_SERVER_CERT = False # ALWAYS SET True in production.
AUTH_LDAP_CA_CERT_PATH = '' # absolute path of cert


# local, full-path location for finding aids to be loaded to eXist via admin interface
FINDINGAID_EAD_SOURCE= '/mnt/entity/staff/Special Collections/EADXML/FinishedMARBL'

# settings for proxy host and site base url; used to configure cache to reload
# a PDF when publishing a new or updated EAD
PROXY_HOST = 'localhost:3128'
SITE_BASE_URL = 'http://localhost:800/'     

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
