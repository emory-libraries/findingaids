from django.conf import settings
from eulcore import xmlmap
from eulcore.xmlmap.eadmap import EncodedArchivalDescription, Component, SubordinateComponents
from eulcore.existdb.query import QuerySet
from eulcore.django.existdb.db import ExistDB
from eulcore.django.existdb.manager import Manager
from eulcore.django.existdb.models import XmlModel


# finding aid model
# currently just a wrapper around ead xmlmap object,
# with a exist queryset initialized using django-exist settings and ead model

class FindingAid(XmlModel, EncodedArchivalDescription):
    """
      Customized version of :class:`eulcore.xmlmap.eadmap.EncodedArchivalDescription` EAD object.

      Additional fields and methods are used for search, browse, and display.
    """
    
    list_title_xpath = "./archdesc/did/origination/node()|./archdesc/did[not(origination/node())]/unittitle"
    
    # field to use for alpha-browse - any origination name, fall back to unit title if no origination
    list_title = xmlmap.StringField(list_title_xpath)
    "list title used for alphabetical browse - any origination name, or unittitle if there is none"
    
    # first letter of title field - using generic descriptor because no string() conversion is needed
    first_letter = xmlmap.ItemField("substring(%s,1,1)" % list_title_xpath)
    "First letter of list title, used to generate list of first-letters for browse."

    objects = Manager('/ead')
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving FindingAid objects
        in eXist.

        Configured to use */ead* as base search path.
    """

    def admin_info(self):
        """
        Generate a list of administrative information fields from the archive description.
        Only includes MARBL-designated fields to be displayed as administrative information,
        in a specified order.  Any fields not present in the finding aid will
        not be included in the list returned.

        These fields are included, in this order:
        access restrictions, use restrictions, alternate form, related material,
        separated material, acquisition info, custodial history, preferred citation

        :rtype: list of :class:`eulcore.xmlmap.eadmap.Section`
        """
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
        """
        Generate a list of collection description fields from the archive description.
        Only includes MARBL-designated fields to be displayed as collection description,
        in a specified order.  Any fields not present in the finding aid will
        not be included in the list returned.

        These fields are included, in this order:
        biography/history, bibliography, scope & content, arrangement, other finding aid

        :rtype: list of :class:`eulcore.xmlmap.eadmap.Section`
        """
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


class Series(XmlModel, Component):
    """
      Top-level (c01) series.

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`
    """
    ead = xmlmap.NodeField("ancestor::ead", FindingAid)
    ":class:`findingaids.fa.models.FindingAid` access to ancestor EAD element"

    parent = xmlmap.NodeField("parent::node", "self")

    objects = Manager('//c01')
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving c01 series objects
        in eXist.

        Configured to use *//c01* as base search path.
    """

    def series_info(self):
        """"
        Generate a list of sereies information fields.
        Only includes MARBL-designated fields to be displayed as part of series 
        description, in a specified order.  Any fields not present in the finding
        aid will not be included in the list returned.

        These fields are included, in this order:
        biography/history, scope & content, arrangement, other finding aid,
        use restrictions, access restrictions, alternate form, location of original,
        bibliography

        :rtype: list of :class:`eulcore.xmlmap.eadmap.Section`
        """
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
        "Series display label - *unitid : unittitle* (if unitid) or *unittitle* (if no unitid)"
        return ': '.join([u for u in [self.did.unitid, self.did.unittitle] if u])

# TODO: how to configure base ead class so component classtype can be overridden ?

# override component.c node_class
# subcomponents need to be initialized as Series to get display_label, series list...
# FIXME: there must be a better way to do this!
Component.c.field.node_class = Series
SubordinateComponents.c.field.node_class = Series


class Subseries(Series):
    """
      c02 level subseries

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`; extends
      :class:`Series`
    """
    series = xmlmap.NodeField("parent::c01", Series)
    ":class:`findingaids.fa.models.Series` access to c01 series this subseries belongs to"
    objects = Manager('//c02')
    """:class:`eulcore.django.existdb.manager.Manager`

        Configured to use *//c02* as base search path.
    """


class Subsubseries(Series):
    """
      c03 level subseries

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`; extends
      :class:`Series`
    """
    subseries = xmlmap.NodeField("parent::c02", Subseries)
    ":class:`findingaids.fa.models.Subseries` access to c02 subseries this sub-subseries belongs to"
    series = xmlmap.NodeField("ancestor::c01", Series)
    ":class:`findingaids.fa.models.Series` access to c01 series this sub-subseries belongs to"
    objects = Manager('//c03')
    """:class:`eulcore.django.existdb.manager.Manager`

        Configured to use *//c03* as base search path.
    """
