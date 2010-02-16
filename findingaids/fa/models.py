from django.conf import settings
from eulcore import xmlmap
from eulcore.xmlmap.eadmap import ead
from eulcore.existdb.query import QuerySet
from eulcore.django.existdb.db import ExistDB 


# finding aid model
# currently just a wrapper around ead xmlmap object,
# with a exist queryset initialized using django-exist settings and ead model

class FindingAid(ead):
    # field to use for alpha-browse - any origination name, fall back to unit title if no origination
    list_title = xmlmap.XPathString("./archdesc/did/origination/node()|./archdesc/did[not(exists(origination/node()))]/unittitle")
    objects = QuerySet(model=ead, xpath="/ead", using=ExistDB(),
                       collection=settings.EXISTDB_ROOT_COLLECTION)

    def admin_info(self):
        # generate a list of admin info fields - to be displayed, in the proper order
        info = []
        if self.archdesc.access_restriction:
            info.append(self.archdesc.access_restriction)
        if self.archdesc.use_restriction:
            info.append(self.archdesc.use_restriction)
        if self.archdesc.alternate_form:
            info.append(self.archdesc.alternate_form)
        if self.archdesc.related_material:
            info.append(self.archdesc.related_material)
        if self.archdesc.separated_material:
            info.append(self.archdesc.separated_material)
        if self.archdesc.acquisition_info:
            info.append(self.archdesc.acquisition_info)
        if self.archdesc.custodial_history:
            info.append(self.archdesc.custodial_history)
        if self.archdesc.preferred_citation:
            info.append(self.archdesc.preferred_citation)
        return info


FindingAid.objects.model = FindingAid


