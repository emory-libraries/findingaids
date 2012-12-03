# file findingaids/settings.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from os import path

import os
os.environ['CELERY_LOADER'] = 'django'
# use a differently-named default queue to keep separate from other projects using celery
CELERY_DEFAULT_QUEUE = 'findingaids'


# Get the directory of this file for relative dir paths.
# Django sets too many absolute paths.
BASE_DIR = path.dirname(path.abspath(__file__))

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'fa.db'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

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
MEDIA_ROOT = path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
)

ROOT_URLCONF = 'findingaids.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'findingaids.wsgi.application'

TEMPLATE_DIRS = [
    path.join(BASE_DIR, 'templates'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
]

# also look for templates in virtualenv
import os
if 'VIRTUAL_ENV' in os.environ:
    genlib_path = os.path.join(os.environ['VIRTUAL_ENV'], 'themes', 'genlib')
    TEMPLATE_DIRS.append(genlib_path)


TEMPLATE_CONTEXT_PROCESSORS = (
    #django default context processors
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    # additional context processors
    "django.core.context_processors.request",  # always include request in render context
    "findingaids.fa.context_processors.searchform",  # search form on every page
    "findingaids.fa.context_processors.version",     # software version on every page
)

# Enable additional backends.
# Enable this for LDAP and see ReadMe for install dependencies.
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',
                           'eullocal.django.emory_ldap.backends.EmoryLDAPBackend')

AUTH_PROFILE_MODULE = 'emory_ldap.EmoryLDAPUserProfile'

LOGIN_URL = "/admin/accounts/login/"
LOGIN_REDIRECT_URL = "/admin/"

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# NOTE: using memory cache for now for simplicity
CACHE_BACKEND = 'locmem://'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'djcelery',
    #'eulcore', # https://svn.library.emory.edu/svn/python-eulcore/
    'eullocal.django.emory_ldap',
    'eullocal.django.taskresult',
    'eullocal.django.util',
    'eulexistdb',
    'eulxml',
    'findingaids.fa',
    'findingaids.fa_admin',
    'findingaids.content',
)

EXTENSION_DIRS = (
    #path.join(BASE_DIR, '../external/django-modules'),
)


EXISTDB_INDEX_CONFIGFILE = path.join(BASE_DIR, "exist_index.xconf")

# explicitly set to false to simplify patching value for tests
CELERY_ALWAYS_EAGER = False

import sys
try:
    sys.path.extend(EXTENSION_DIRS)
except NameError:
    pass  # EXTENSION_DIRS not defined. This is OK; we just won't use it.
del sys

try:
    from localsettings import *
except ImportError:
    import sys
    print >>sys.stderr, 'No local settings. Trying to start, but if ' + \
        'stuff blows up, try copying localsettings-sample.py to ' + \
        'localsettings.py and setting appropriately for your environment.'
    pass

TEST_RUNNER = 'eulexistdb.testutil.ExistDBTextTestSuiteRunner'

try:
    # use xmlrunner if it's installed; default runner otherwise. download
    # it from http://github.com/danielfm/unittest-xml-reporting/ to output
    # test results in JUnit-compatible XML.
    import xmlrunner
    TEST_RUNNER = 'eulexistdb.testutil.ExistDBXmlTestSuiteRunner'
    TEST_OUTPUT_DIR='test-results'
except ImportError:
    pass

