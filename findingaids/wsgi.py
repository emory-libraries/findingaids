import os
import djcelery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findingaids.settings')
os.environ['PYTHON_EGG_CACHE'] = '/tmp'

# Only set a default proxy if there is not already one in the env.
# For production environments, proxy should be set in apache environment.
# if 'HTTP_PROXY' not in os.environ:
#     os.environ['HTTP_PROXY'] = 'http://localhost:3128/'

os.environ['VIRTUAL_ENV'] = '/home/httpd/findingaids/env/'

djcelery.setup_loader()

# from django.core.handlers.wsgi import WSGIHandler
# application = WSGIHandler()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
