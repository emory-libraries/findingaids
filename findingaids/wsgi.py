import os
import djcelery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findingaids.settings')
os.environ['PYTHON_EGG_CACHE'] = '/tmp'
os.environ['VIRTUAL_ENV'] = '/home/httpd/findingaids/env/'

djcelery.setup_loader()

# from django.core.handlers.wsgi import WSGIHandler
# application = WSGIHandler()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
