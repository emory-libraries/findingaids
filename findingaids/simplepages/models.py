from django.db import models
from django.contrib.flatpages.models import FlatPage

class SimplePage(FlatPage):
    # Adding a few other small fields to the FlatPage model for tracking.
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True, auto_now_add=True)