# file findingaids/fa/models.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from datetime import datetime

from django.contrib import admin
from django.core.cache import cache
from django.db import models

from eulxml import xmlmap
from eulxml.xmlmap.eadmap import EncodedArchivalDescription, Component, \
    SubordinateComponents, Index as EadIndex, ArchivalDescription, EAD_NAMESPACE, \
    UnitTitle, Section, XLINK_NAMESPACE
from eulexistdb.manager import Manager
from eulexistdb.models import XmlModel


# finding aid models

ID_DELIMITER = '_'


class FindingAid(XmlModel, EncodedArchivalDescription):
    """
    Customized version of :class:`eulxml.EncodedArchivalDescription` EAD object.

    Additional fields and methods are used for search, browse, and display.
    """
    ROOT_NAMESPACES = {
        'e': EAD_NAMESPACE,
        'exist': 'http://exist.sourceforge.net/NS/exist',
        'util': 'http://exist-db.org/xquery/util',
    }
    # redeclaring namespace from eulcore to ensure prefix is correct for xpaths

    # NOTE: overridding these fields from EncodedArchivalDescription to allow
    # for efficiently retrieving unittitle and abstract in the full document OR
    # in the constructed return object returned from eXist for search/browse
    unittitle = xmlmap.NodeField('.//e:unittitle[not(ancestor::e:dsc)]', UnitTitle)
    abstract = xmlmap.NodeField('.//e:abstract[not(ancestor::e:dsc)]', xmlmap.XmlObject)
    physical_descriptions = xmlmap.StringListField('.//e:physdesc[not(ancestor::e:dsc)]', normalize=True)

    list_title_xpaths = ["e:archdesc/e:did/e:origination/e:corpname",
        "e:archdesc/e:did/e:origination/e:famname",
        "e:archdesc/e:did/e:origination/e:persname",
        "e:archdesc/e:did[not(e:origination/e:corpname or e:origination/e:famname or e:origination/e:persname)]/e:unittitle"]
    list_title_xpath = "|".join("./%s" % xp for xp in list_title_xpaths)
    #./archdesc/did/origination/node()|./archdesc/did[not(origination/node())]/unittitle"

    # field to use for alpha-browse - any origination name, fall back to unit title if no origination
    list_title = xmlmap.NodeField(list_title_xpath, xmlmap.XmlObject)
    "list title used for alphabetical browse - any origination name, or unittitle if there is none"

    # first letter of title field
    first_letter = xmlmap.StringField("substring(normalize-space(%s),1,1)" % list_title_xpath)
    "First letter of list title"

    dc_subjects = xmlmap.StringListField('e:archdesc//e:controlaccess/e:subject[@encodinganalog = "650"] | \
            e:archdesc//e:controlaccess/e:persname[@encodinganalog = "600"] | \
            e:archdesc//e:controlaccess/e:corpname[@encodinganalog = "610"] | \
            e:archdesc//e:controlaccess/e:corpname[@encodinganalog = "611"] | \
            e:archdesc//e:controlaccess/e:geogname[@encodinganalog = "651"]', normalize=True)
    "control access fields that should be mapped to Dublin Core subject, based on encodinganalog attribute"

    dc_contributors = xmlmap.StringListField('e:archdesc//e:controlaccess/e:persname[@encodinganalog = "700"] | \
        e:archdesc//e:controlaccess/e:corpname[@encodinganalog = "710"]', normalize=True)
    "control access fields that should be mapped to Dublin Core contributor, based on encodinganalog attribute"

    # convenience mapping for searching on subject fields
    subject = xmlmap.StringField('.//e:controlaccess')

    # local repository *subarea* - e.g., MARBL, University Archives
    repository = xmlmap.StringListField('.//e:subarea')

    # boosted fields in the index: must be searched to get proper relevance score
    boostfields = xmlmap.StringField('.//e:titleproper | .//e:origination | \
        .//e:abstract | .//e:bioghist | .//e:scopecontent | .//e:controlaccess')

    # temporary manual mapping for processinfo, will be incorporated into a release of eulxml
    process_info = xmlmap.NodeField("e:archdesc/e:processinfo", Section)

    # match-count on special groups of data for table of contents listing
    # - administrative info fields
    _admin_info = ['userestrict', 'altformavail', 'relatedmaterial', 'separatedmaterial',
        'acqinfo', 'custodhist', 'prefercite']
    # -- map as regular xmlmap field, for use when entire object is returned
    admin_info_matches = xmlmap.IntegerField('count(./e:archdesc/*[' +
        '|'.join(['self::e:%s' % field for field in _admin_info]) + ']//exist:match)')
    # -- eXist-specific xpath for returning count without entire document
    admin_info_matches_xpath = 'count(util:expand(%(xq_var)s/e:archdesc/(' + \
        '|'.join(['e:%s' % field for field in _admin_info]) + '))//exist:match)'
    # - collection description fields
    _coll_desc = ['bioghist', 'bibliography', 'scopecontent', 'arrangement', 'otherfindaid']
    # -- map as regular xmlmap field, for use when entire object is returned
    coll_desc_matches = xmlmap.IntegerField('count(' +
        '|'.join('./e:archdesc/e:%s//exist:match' % field for field in _coll_desc) + ')')
    # -- eXist-specific xpath for returning count without entire document
    coll_desc_matches_xpath = 'count(util:expand(%(xq_var)s/e:archdesc/(' +  \
        '|'.join('e:%s' % field for field in _coll_desc) + '))//exist:match)'
    # - controlaccess match-count
    controlaccess_matches_xpath = 'count(util:expand(%(xq_var)s/e:archdesc/e:controlaccess)//exist:match)'

    objects = Manager('/e:ead')
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
        if self.process_info:
            info.append(self.process_info)
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
        fields["identifier"] = set([self.eadid.url])

        return fields


class ListTitle(XmlModel):
    # EAD list title - used to retrieve at the title level for better query response
    ROOT_NAMESPACES = {'e': EAD_NAMESPACE}
    xpath = "|".join("//%s" % xp for xp in FindingAid.list_title_xpaths)
    # xpath to use for alpha-browse - using list title xpaths from FindingAid

    # first letter of list title field (using generic item field to avoid string() conversion)
    first_letter = xmlmap.ItemField("substring(.,1,1)")
    "First letter of a finding aid list title: use to generate list of first-letters for browse."
    objects = Manager(xpath)


def title_letters():
    """Cached list of distinct, sorted first letters present in all Finding Aid titles.
    Cached results should be refreshed after half an hour."""
    cache_key = 'browse-title-letters'
    if cache.get(cache_key) is None:
        letters = ListTitle.objects.only('first_letter').order_by('first_letter').distinct()
        cache.set(cache_key, list(letters))  # use configured cache timeout
    return cache.get(cache_key)


class EadRepository(XmlModel):
    ROOT_NAMESPACES = {'e': EAD_NAMESPACE}
    normalized = xmlmap.StringField('normalize-space(.)')
    objects = Manager('//e:subarea')

    @staticmethod
    def distinct():
        """Cached list of distinct owning repositories in all Finding Aids."""
        cache_key = 'findingaid-repositories'
        if cache.get(cache_key) is None:
            # using normalized version because whitespace is inconsistent in this field
            repos = EadRepository.objects.only('normalized').distinct()
            cache.set(cache_key, list(repos))  # use configured default cache timeout
        return cache.get(cache_key)


class LocalComponent(Component):
    '''Extend default :class:`eulcore.xmlmap.eadmap.Component` class to add a
    method to detect first file-item in a list.  (Needed for container list display
    in templates).'''
    ROOT_NAMESPACES = {
        'e': EAD_NAMESPACE,
    }
    # by local convention, section headers are sibling components with no containers
    preceding_files = xmlmap.NodeListField('preceding-sibling::node()[@level="file"][e:did/e:container]', "self")

    @property
    def first_file_item(self):
        'Boolean: True if this component is the first file item in a series/container list'
        return len(self.did.container) and len(self.preceding_files) == 0


class Series(XmlModel, LocalComponent):
    """
      Top-level (c01) series.

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`
    """

    ROOT_NAMESPACES = {
        'e': EAD_NAMESPACE,
        'exist': 'http://exist.sourceforge.net/NS/exist'
    }

    ead = xmlmap.NodeField("ancestor::e:ead", FindingAid)
    ":class:`findingaids.fa.models.FindingAid` access to ancestor EAD element"

    parent = xmlmap.NodeField("parent::node()", "self")

    objects = Manager('//e:c01')
    # NOTE: this element should not be restricted by level=series because eXist full-text indexing
    # is more efficient if the queried element matches the indexed element
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving c01 series objects
        in eXist.

        Configured to use *//c01* as base search path.
    """

    match_count = xmlmap.IntegerField("count(.//exist:match)")
    ":class:`findingaids.fa.models.FindingAid` number of keyword matchs"

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
        if self.related_material:
            fields.append(self.related_material)

        return fields

    def display_label(self):
        "Series display label - *unitid : unittitle* (if unitid) or *unittitle* (if no unitid)"
        return ': '.join([unicode(u) for u in [self.did.unitid, self.did.unittitle] if u])

    _short_id = None

    @property
    def short_id(self):
        "Short-form id (without eadid prefix) for use in external urls."
        if self._short_id is None:
            # get eadid, if available
            if hasattr(self, 'ead') and hasattr(self.ead, 'eadid') and self.ead.eadid.value:
                eadid = self.ead.eadid.value
            else:
                eadid = None
            self._short_id = shortform_id(self.id, eadid)
        return self._short_id

# override component.c node_class
# subcomponents need to be initialized as Series to get display_label, series list...
# FIXME: look for a a better way to do this kind of XmlObject extension
Component._fields['c'].node_class = Series
SubordinateComponents._fields['c'].node_class = Series


def shortform_id(id, eadid=None):
    """Calculate a short-form id (without eadid prefix) for use in external urls.
    Uses eadid if available; otherwise, relies on the id delimiter character.
    :param id: id to be shortened
    :param eadid: eadid prefix, if available
    :returns: short-form id
    """
    # if eadid is available, use that (should be the most reliable way to shorten id)
    if eadid:
        id = id.replace('%s_' % eadid, '')

    # if eadid is not available, split on _ and return latter portion
    elif ID_DELIMITER in id:
        eadid, id = id.split(ID_DELIMITER)

    # this shouldn't happen -  one of the above two options should work
    else:
        raise Exception("Cannot calculate short id for %s" % id)
    return id


class Series2(Series):
    """
      c02 level subseries

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`; extends
      :class:`Series`
    """
    series = xmlmap.NodeField("parent::e:c01", Series)
    ":class:`findingaids.fa.models.Series` access to c01 series this subseries belongs to"
    objects = Manager('//e:c02')
    """:class:`eulcore.django.existdb.manager.Manager`

        Configured to use *//c02* as base search path.
    """


class Series3(Series):
    """
      c03 level subseries

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`; extends
      :class:`Series`
    """
    series2 = xmlmap.NodeField("parent::e:c02", Series2)
    ":class:`findingaids.fa.models.Subseries` access to c02 subseries this sub-subseries belongs to"
    series = xmlmap.NodeField("ancestor::e:c01", Series)
    ":class:`findingaids.fa.models.Series` access to c01 series this sub-subseries belongs to"
    objects = Manager('//e:c03')
    """:class:`eulcore.django.existdb.manager.Manager`

        Configured to use *//c03* as base search path.
    """


class Index(XmlModel, EadIndex):
    """
      EAD Index, with index entries.

      Customized version of :class:`eulcore.xmlmap.eadmap.Index`
    """

    ROOT_NAMESPACES = {
        'e': EAD_NAMESPACE,
        'xlink': XLINK_NAMESPACE,
        'exist': 'http://exist.sourceforge.net/NS/exist'
    }

    ead = xmlmap.NodeField("ancestor::e:ead", FindingAid)
    ":class:`findingaids.fa.models.FindingAid` access to ancestor EAD element"

    parent = xmlmap.NodeField("parent::node()", "self")

    objects = Manager('//e:index')
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving index objects
        in eXist.

        Configured to use *//index* as base search path.
    """

    match_count = xmlmap.IntegerField("count(.//exist:match)")

    _short_id = None

    @property
    def short_id(self):
        "Short-form id (without eadid prefix) for use in external urls."
        if self._short_id is None:
            # get eadid, if available
            if hasattr(self, 'ead') and hasattr(self.ead, 'eadid') and self.ead.eadid.value:
                eadid = self.ead.eadid.value
            else:
                eadid = None
            self._short_id = shortform_id(self.id, eadid)
        return self._short_id


# FIXME: look for a a better way to do this kind of XmlObject extension
ArchivalDescription._fields['index'].node_class = Index


class FileComponent(XmlModel, Component):
    """
    Any EAD component with a level of *file*, with item-level information (box &
    folder contents).
    """

    ROOT_NAMESPACES = {
        'e': EAD_NAMESPACE,
        'xlink': XLINK_NAMESPACE,
        'exist': 'http://exist.sourceforge.net/NS/exist'
    }

    ead = xmlmap.NodeField("ancestor::e:ead", FindingAid)
    ":class:`findingaids.fa.models.FindingAid` access to ancestor EAD element"

    # NOTE: mapping parent, series1, and series2 to ensure there is enough
    # information to generate a link to the series a FileComponent belongs to

    parent = xmlmap.NodeField("parent::node()", Series)
    ":class:`findingaids.fa.models.Series` series this file belongs to (could be c01, c02, or c03)."

    series1 = xmlmap.NodeField("ancestor::e:c01", Series)
    ":class:`findingaids.fa.models.Series` c01 series this file belongs to."

    series2 = xmlmap.NodeField("ancestor::e:c02", Series)
    ":class:`findingaids.fa.models.Series` c02 series this file belongs to, if any."

    objects = Manager('''(e:ead//e:c01|e:ead//e:c02|e:ead//e:c03|e:ead//e:c04)[@level="file"]''')
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving c-series file objects
        in eXist.

        Configured to find any c-series (1-4) with a level of file.
    """


class Deleted(models.Model):
    """
    Information about a previously published finding aid that has been deleted.
    """
    eadid = models.CharField('EAD Identifier', max_length=50, unique=True)
    title = models.CharField(max_length=200)
    date = models.DateTimeField('Date removed', default=datetime.now())
    note = models.CharField(max_length=400, blank=True,
            help_text="Optional: Enter the reason this document is being deleted. " +
                      "These comments will be displayed to anyone who had the finding " +
                      "aid bookmarked and returns after it is gone.")
    class Meta:
        verbose_name = 'Deleted Record'

    def __unicode__(self):
        return self.eadid


class DeletedAdmin(admin.ModelAdmin):
    list_display = ('eadid', 'title', 'date', 'note')
    list_filter = ('date',)

    # don't allow creating deleted records via admin site
    def has_add_permission(self, request):
        return False


admin.site.register(Deleted, DeletedAdmin)
