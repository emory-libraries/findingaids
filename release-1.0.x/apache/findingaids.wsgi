import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'findingaids.settings'
os.environ['PYTHON_EGG_CACHE'] = '/tmp'
os.environ['HTTP_PROXY'] = 'http://spiderman.library.emory.edu:3128/'
os.environ['VIRTUAL_ENV'] = '/home/httpd/findingaids/env/'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()