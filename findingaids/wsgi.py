import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findingaids.settings')
os.environ['PYTHON_EGG_CACHE'] = '/tmp'
os.environ['HTTP_PROXY'] = 'http://localhost:3128/'
os.environ['VIRTUAL_ENV'] = '/home/httpd/findingaids/env/'

# from django.core.handlers.wsgi import WSGIHandler
# application = WSGIHandler()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
