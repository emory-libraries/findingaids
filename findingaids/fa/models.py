from django.conf import settings
from eulcore import xmlmap
from eulcore.xmlmap.eadmap import EncodedArchivalDescription, Component, SubordinateComponents
from eulcore.existdb.query import QuerySet
from eulcore.django.existdb.db import ExistDB


# finding aid model
# currently just a wrapper around ead xmlmap object,
# with a exist queryset initialized using django-exist settings and ead model


class FindingAid(EncodedArchivalDescription):
    """
      Customized version of eulcore.xmlmap.eadmap EAD object
    """
    
    list_title_xpath = "./archdesc/did/origination/node()|./archdesc/did[not(origination/node())]/unittitle"
    
    # field to use for alpha-browse - any origination name, fall back to unit title if no origination
    list_title = xmlmap.XPathString(list_title_xpath)
    # first letter of title field - using generic descriptor because no string() conversion is needed
    first_letter = xmlmap.XPathItem("substring(%s,1,1)" % list_title_xpath)
    objects = QuerySet(model=EncodedArchivalDescription, xpath="/ead", using=ExistDB(),
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

    def collection_description(self):
        # generate a list of collection description fields - to be displayed, in the proper order
        fields = []
        if self.archdesc.biography_history:
            fields.append(self.archdesc.biography_history)
        if self.archdesc.bibliography:
            fields.append(self.archdesc.bibliography)
        if self.archdesc.scope_content:
            fields.append(self.archdesc.scope_content)
        if self.archdesc.arrangement:
            fields.append(self.archdesc.arrangement)
        if self.archdesc.other:
            fields.append(self.archdesc.other)

        return fields


FindingAid.objects.model = FindingAid


class Series(Component):
    "c01 level series"
    ead = xmlmap.XPathNode("ancestor::ead", FindingAid)
    objects = QuerySet(model=Component, xpath="//c01", using=ExistDB(), 
                       collection=settings.EXISTDB_ROOT_COLLECTION)

    def series_info(self):
        "Return whatever series information is present, in display order."
        fields = []
        if self.biography_history:
            fields.append(self.biography_history)
        if self.scope_content:
            fields.append(self.scope_content)
        if self.arrangement:
            fields.append(self.arrangement)
        if self.other:
            fields.append(self.other)
        if self.use_restriction:
            fields.append(self.use_restrict)
        if self.access_restriction:
            fields.append(self.access_restriction)
        if self.alternate_form:
            fields.append(self.alternate_form)
        if self.originals_location:
            fields.append(self.originals_location)
        if self.bibliography:
            fields.append(self.bibliography)

        return fields

    def display_label(self):
        "Series display label - *unitid : unittitle* (if unitid) or *unittitle* (no unitid)"
        return ': '.join([u for u in [self.did.unitid, self.did.unittitle] if u])

# TODO: how to configure base ead class so component classtype can be overridden ?

Series.objects.model = Series
# override component.c node_class
# subcomponents need to be initialized as Series to get display_label, series list...
# FIXME: there must be a better way to do this!
Component.c = xmlmap.XPathNodeList("c02|c03|c04|c05|c06|c07|c08|c09|c10|c11|c12", Series)
SubordinateComponents.c = xmlmap.XPathNodeList("c01", Series)
Series.parent = xmlmap.XPathNode("parent::node", Series)       # arg: for subseries

class Subseries(Series):
    "c02 level series"
    series = xmlmap.XPathNode("parent::c01", Series) 
    objects = QuerySet(model=Component, xpath="//c02", using=ExistDB(), 
                       collection=settings.EXISTDB_ROOT_COLLECTION)

Subseries.objects.model = Subseries

class Subsubseries(Series):
    "c03 level series"
    subseries = xmlmap.XPathNode("parent::c02", Subseries)
    series = xmlmap.XPathNode("ancestor::c01", Series)
    objects = QuerySet(model=Component, xpath="//c03", using=ExistDB(),
                       collection=settings.EXISTDB_ROOT_COLLECTION)

Subsubseries.objects.model = Subsubseries
