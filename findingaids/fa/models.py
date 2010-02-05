from django.conf import settings
from eulcore.xmlmap.eadmap import ead
from eulcore.existdb.query import QuerySet
from eulcore.django.existdb.db import ExistDB 


# finding aid model
# currently just a wrapper around ead xmlmap object,
# with a exist queryset initialized using django-exist settings and ead model

class FindingAid(ead):
    objects = QuerySet(model=ead, xpath="/ead", using=ExistDB(),
                       collection=settings.EXISTDB_ROOT_COLLECTION)
