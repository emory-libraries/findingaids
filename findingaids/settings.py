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

import djcelery
djcelery.setup_loader()


SECRET_KEY = "123134f2ewf13rf2qewf24qf4f2wf32qfq4"
# explicitly set celery task to findingaids queue (let celery create the queue)
CELERY_ROUTES = {
    'findingaids.fa_admin.tasks.reload_cached_pdf': {'queue': 'findingaids-zo'},
    'findingaids.fa_admin.tasks.archive_svn_checkout': {'queue': 'findingaids-zo'}
}

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

# Absolute path to media directory
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'sitemedia')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
# NOTE: user-uploaded media currently unused in this site
# MEDIA_URL = '/media'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, '..', 'sitemedia'),
]
if 'VIRTUAL_ENV' in os.environ:
    STATICFILES_DIRS.append(os.path.join(os.environ['VIRTUAL_ENV'], 'themes', 'genlib'))

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'findingaids.rdf_middleware.RDFaMiddleware'
)

ROOT_URLCONF = 'findingaids.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'findingaids.wsgi.application'

TEMPLATE_DIRS = [
    path.join(BASE_DIR, '..', 'templates'),
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
    # django default context processors
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    # additional context processors
    "django.core.context_processors.request",  # always include request in render context
    "findingaids.fa.context_processors.searchform",  # search form on every page
    "findingaids.fa.context_processors.common_settings",
)

# Enable additional backends.
# Enable this for LDAP and see ReadMe for install dependencies.
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_ldap.backend.LDAPBackend'
)

LOGIN_URL = "/admin/accounts/login/"
LOGIN_REDIRECT_URL = "/admin/"

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# NOTE: using memory cache for now for simplicity
CACHE_BACKEND = 'locmem://'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'djcelery',
    'eullocal.django.emory_ldap',
    'eullocal.django.taskresult',
    'eullocal.django.util',
    'eulexistdb',
    'eulxml',
    'findingaids.fa',
    'findingaids.fa_admin',
    'findingaids.content',
]


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
        'stuff blows up, try copying localsettings.py.dist to ' + \
        'localsettings.py and setting appropriately for your environment.'
    pass

# django_nose configurations
django_nose = None
try:
    # NOTE: errors if DATABASES is not configured (in some cases),
    # so this must be done after importing localsettings
    import django_nose
except ImportError:
    pass

# - only if django_nose is installed, so it is only required for development
if django_nose is not None:
    INSTALLED_APPS.append('django_nose')
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    NOSE_PLUGINS = [
        'findingaids.testutil.ExistDBSetUp',
        # ...
    ]
    NOSE_ARGS = ['--with-existdbsetup']

# as a fall-back, use existdb test runner to avoid running tests
# against non-test configured existdb collection
else:
    TEST_RUNNER = 'eulexistdb.testutil.ExistDBTextTestSuiteRunner'

# enable django-debug-toolbar when available & in debug/dev modes
if DEBUG or DEV_ENV:
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
    except ImportError:
        pass

# configure: default toolbars + existdb query panel
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'eulexistdb.debug_panel.ExistDBPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]
