# Django settings for findingaids project.
from os import path

# Get the directory of this file for relative dir paths.
# Django sets too many absolute paths.
BASE_DIR = path.dirname(path.abspath(__file__))

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ha=7$wd7wq7n)8!#h&qn_%0*rul!ez*h-xm#v)l$wg&5nkjk%7'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'findingaids.urls'

TEMPLATE_DIRS = (
    path.join(BASE_DIR, 'templates'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
#    'django.contrib.auth',
#    'django.contrib.contenttypes',
#    'django.contrib.sessions',
#    'django.contrib.sites',
    'eulcore', # https://svn.library.emory.edu/svn/python-eulcore/
    'eulcore.django.testsetup',
    'eulcore.django.existdb',
    'eulcore.django.util',
    'findingaids.fa',
)

EXTENSION_DIRS = (
    path.join(BASE_DIR, '../external/django-modules'),
)


EXISTDB_INDEX_CONFIGFILE = path.join(BASE_DIR, "exist_index.xconf")

import sys
try:
    sys.path.extend(EXTENSION_DIRS)
except NameError:
    pass # EXTENSION_DIRS not defined. This is OK; we just won't use it.
del sys

try:
    from localsettings import *
except ImportError:
    import sys
    print >>sys.stderr, 'No local settings. Trying to start, but if ' + \
        'stuff blows up, try copying localsettings-sample.py to ' + \
        'localsettings.py and setting appropriately for your environment.'
    pass

try:
    # use xmlrunner if it's installed; default runner otherwise. download
    # it from http://github.com/danielfm/unittest-xml-reporting/ to output
    # test results in JUnit-compatible XML.
    import xmlrunner
    TEST_RUNNER='xmlrunner.extra.djangotestrunner.run_tests'
    TEST_OUTPUT_DIR='test-results'
except ImportError:
    pass

