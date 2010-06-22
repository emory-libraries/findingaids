from settings import *

# this setting is needed for unit tests involving celery tasks
# so the test doesn't hang
# NOTE: this setting must be set before other things happen or it doesn't work
CELERY_ALWAYS_EAGER = True

