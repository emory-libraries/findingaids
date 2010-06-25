from eulcore import xmlmap
from eulcore.xmlmap.eadmap import EncodedArchivalDescription, Component, SubordinateComponents, Index as EadIndex
from eulcore.django.existdb.manager import Manager
from eulcore.django.existdb.models import XmlModel
from django.db import models
from datetime import datetime


# finding aid model
# currently just a wrapper around ead xmlmap object,
# with a exist queryset initialized using django-exist settings and ead model

class FindingAid(XmlModel, EncodedArchivalDescription):
    """Customized version of :class:`eulcore.xmlmap.eadmap.EncodedArchivalDescription` EAD object.

      Additional fields and methods are used for search, browse, and display.
    """

    list_title_xpaths = ["archdesc/did/origination/corpname",
        "archdesc/did/origination/famname",
        "archdesc/did/origination/persname",
        "archdesc/did[not(origination/corpname or origination/famname or origination/persname)]/unittitle"]
    list_title_xpath = "|".join("./%s" % xp for xp in list_title_xpaths)
    #./archdesc/did/origination/node()|./archdesc/did[not(origination/node())]/unittitle"

    # field to use for alpha-browse - any origination name, fall back to unit title if no origination
    list_title = xmlmap.NodeField(list_title_xpath, xmlmap.XmlObject)
    "list title used for alphabetical browse - any origination name, or unittitle if there is none"

    # first letter of title field
    first_letter = xmlmap.StringField("substring(%s,1,1)" % list_title_xpath)
    "First letter of list title"

    dc_subjects = xmlmap.StringListField ('archdesc//controlaccess/subject[@encodinganalog = "650"] | \
            archdesc//controlaccess/persname[@encodinganalog = "600"] | \
            archdesc//controlaccess/corpname[@encodinganalog = "610"] | \
            archdesc//controlaccess/corpname[@encodinganalog = "611"] | \
            archdesc//controlaccess/geogname[@encodinganalog = "651"]', normalize=True)
    "control access fields that should be mapped to Dublin Core subject, based on encodinganalog attribute"

    dc_contributors = xmlmap.StringListField ('archdesc//controlaccess/persname[@encodinganalog = "700"] | \
        archdesc//controlaccess/corpname[@encodinganalog = "710"]', normalize=True)
    "control access fields that should be mapped to Dublin Core contributor, based on encodinganalog attribute"

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

    def dc_fields(self):
        """
        Generate a dictionary of Dublin Core fields from an EAD.
        Dictionary key: base name of a Dublin Core field (e.g., creator, title)
        Dictionary value: a list of values corresponding to the DC field.
                    Note that some keys may have empty lists as their values.
                    
        :rtype: dict
        """
        fields = dict()
        fields["title"] = set([self.title, self.unittitle])
        fields["creator"] = set([name for name in [self.archdesc.origination] if name])
        fields["publisher"] = set([self.file_desc.publication.publisher])
        fields["date"] = set([date.normalized for date in [self.profiledesc.date] if date])
        fields["language"] = set(self.profiledesc.language_codes)
        fields["subject"] = set(self.dc_subjects)
        fields["contributor"] = set(self.dc_contributors)
        fields["identifier"] = set([self.eadid])
        
        return fields

class ListTitle(XmlModel):
    # EAD list title - used to retrieve at the title level for better query response

    xpath = "|".join("//%s" % xp for xp in FindingAid.list_title_xpaths)    
    # xpath to use for alpha-browse - using list title xpaths from FindingAid
    
    # first letter of list title field (using generic item field to avoid string() conversion)
    first_letter = xmlmap.ItemField("substring(.,1,1)")
    "First letter of a finding aid list title: use to generate list of first-letters for browse."
    objects = Manager(xpath)

def title_letters():
    "List of distinct, sorted first letters present in all Finding Aid titles."
    return ListTitle.objects.only('first_letter').order_by('first_letter').distinct()


class Series(XmlModel, Component):
    """
      Top-level (c01) series.

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`
    """
    ead = xmlmap.NodeField("ancestor::ead", FindingAid)
    ":class:`findingaids.fa.models.FindingAid` access to ancestor EAD element"

    parent = xmlmap.NodeField("parent::node()", "self")

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
            fields.append(self.use_restriction)
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
        return ': '.join([u for u in [self.did.unitid, unicode(self.did.unittitle)] if u])

# override component.c node_class
# subcomponents need to be initialized as Series to get display_label, series list...
# FIXME: look for a a better way to do this kind of XmlObject extension
Component._fields['c'].node_class = Series
SubordinateComponents._fields['c'].node_class = Series


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

class Index(XmlModel, EadIndex):
    """
      EAD Index, with index entries.

      Customized version of :class:`eulcore.xmlmap.eadmap.Index`
    """
    ead = xmlmap.NodeField("ancestor::ead", FindingAid)
    ":class:`findingaids.fa.models.FindingAid` access to ancestor EAD element"

    parent = xmlmap.NodeField("parent::node()", "self")

    objects = Manager('//index')
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving index objects
        in eXist.

        Configured to use *//index* as base search path.
    """

class Deleted(models.Model):
    """
    Information about a previously published finding aid that has been deleted.
    """
    eadid = models.CharField('EAD Identifier', max_length=50)
    title = models.CharField(max_length=200)
    date_time = models.DateTimeField('Date and time of record deletion', default=datetime.now())
    comments = models.CharField(max_length=400, blank=True, 
            help_text="Optional: Enter the reason this document is being deleted. " +
                      "These comments will be displayed to anyone who had the finding " +
                      "aid bookmarked and returns after it is gone.")
