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
import logging
import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models

from eulxml import xmlmap
from eulxml.xmlmap import eadmap
from eulexistdb.manager import Manager
from eulexistdb.models import XmlModel

from findingaids.utils import normalize_whitespace


# logging
logger = logging.getLogger(__name__)


# finding aid models

ID_DELIMITER = '_'

class DigitalArchivalObject(eadmap.DigitalArchivalObject):
    show = xmlmap.StringField("@xlink:show")
    'attribute to determine how the resource should be displayed'


class Name(XmlModel):
    '''XmlObject for a generic name in an EAD document.  Includes common
    functionality for persname, famname, corpname, and geogname.
    '''
    ROOT_NS = eadmap.EAD_NAMESPACE
    ROOT_NAMESPACES = {
        'e': eadmap.EAD_NAMESPACE,
    }
    source = xmlmap.StringField('@source')
    role = xmlmap.StringField('@role')
    authfilenumber = xmlmap.StringField('@authfilenumber')
    encodinganalog = xmlmap.StringField('@encodinganalog')
    value = xmlmap.StringField(".", normalize=True)
    # NOTE: could be persname, corpname, famname

    @property
    def is_personal_name(self):
        'boolean indicator if this is a persname tag'
        return self.node.tag == "{%s}persname" % eadmap.EAD_NAMESPACE

    @property
    def is_corporate_name(self):
        'boolean indicator if this is a corpname tag'
        return self.node.tag == "{%s}corpname" % eadmap.EAD_NAMESPACE

    @property
    def is_family_name(self):
        'boolean indicator if this is a famname tag'
        return self.node.tag == "{%s}famname" % eadmap.EAD_NAMESPACE

    @property
    def is_geographic_name(self):
        'boolean indicator if this is a geogname tag'
        return self.node.tag == "{%s}geogname" % eadmap.EAD_NAMESPACE

    @property
    def uri(self):
        ''''Generate a URI for this name if possible, based on source and
        authfilenumber attributes.  Currently supports viaf, geonames,
        and dbpedia sources.
        '''
        if self.source == 'viaf':
            return 'http://viaf.org/viaf/%s' % self.authfilenumber
        elif self.source == 'geonames':
            return 'http://sws.geonames.org/%s/' % self.authfilenumber
        elif self.source == 'dbpedia':
            return 'http://dbpedia.org/resource/%s' % self.authfilenumber


class FindingAid(XmlModel, eadmap.EncodedArchivalDescription):
    """
    Customized version of :class:`eulxml.EncodedArchivalDescription` EAD object.

    Additional fields and methods are used for search, browse, and display.
    """
    ROOT_NAMESPACES = {
        'e': eadmap.EAD_NAMESPACE,
        'xlink': eadmap.XLINK_NAMESPACE,
        'exist': 'http://exist.sourceforge.net/NS/exist',
        'util': 'http://exist-db.org/xquery/util',
    }
    # redeclaring namespace from eulcore to ensure prefix is correct for xpaths

    # NOTE: overridding these fields from EncodedArchivalDescription to allow
    # for efficiently retrieving unittitle and abstract in the full document OR
    # in the constructed return object returned from eXist for search/browse
    unittitle = xmlmap.NodeField('.//e:unittitle[not(ancestor::e:dsc)]', eadmap.UnitTitle)
    abstract = xmlmap.NodeField('.//e:abstract[not(ancestor::e:dsc)]', xmlmap.XmlObject)
    physical_descriptions = xmlmap.StringListField('.//e:physdesc[not(ancestor::e:dsc)]', normalize=True)

    list_title_xpaths = [
        "e:archdesc/e:did/e:origination/e:corpname",
        "e:archdesc/e:did/e:origination/e:famname",
        "e:archdesc/e:did/e:origination/e:persname",
        "e:archdesc/e:did[count(e:origination/e:corpname|e:origination/e:famname|e:origination/e:persname) = 0]/e:unittitle"
    ]
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
    repository = xmlmap.StringListField('.//e:subarea', normalize=True)

    # boosted fields in the index: must be searched to get proper relevance score
    boostfields = xmlmap.StringField('.//e:titleproper | .//e:origination | \
        .//e:abstract | .//e:bioghist | .//e:scopecontent | .//e:controlaccess')

    # temporary manual mapping for processinfo, will be incorporated into a release of eulxml
    process_info = xmlmap.NodeField("e:archdesc/e:processinfo", eadmap.Section)

    # is mapped as single in eulxml.eadmap but could be multiple
    separatedmaterial_list = xmlmap.NodeListField("e:archdesc/e:separatedmaterial", eadmap.Section)
    relatedmaterial_list = xmlmap.NodeListField("e:archdesc/e:relatedmaterial", eadmap.Section)

    # match-count on special groups of data for table of contents listing
    # - administrative info fields
    _admin_info = ['userestrict', 'altformavail', 'relatedmaterial', 'separatedmaterial',
                   'acqinfo', 'custodhist', 'prefercite']


    # -- map as regular xmlmap field, for use when entire object is returned
    admin_info_matches = xmlmap.IntegerField(
        'count(./e:archdesc/*[' +
        '|'.join(['self::e:%s' % field for field in _admin_info]) + ']//exist:match)')
    # -- eXist-specific xpath for returning count without entire document
    admin_info_matches_xpath = 'count(util:expand(%(xq_var)s/e:archdesc/(' + \
        '|'.join(['e:%s' % field for field in _admin_info]) + '))//exist:match)'
    # - collection description fields
    _coll_desc = ['bioghist', 'bibliography', 'scopecontent', 'arrangement', 'otherfindaid']
    # -- map as regular xmlmap field, for use when entire object is returned
    coll_desc_matches = xmlmap.IntegerField(
        'count(' + '|'.join('./e:archdesc/e:%s//exist:match' % field for field in _coll_desc) + ')')
    # -- eXist-specific xpath for returning count without entire document
    coll_desc_matches_xpath = 'count(util:expand(%(xq_var)s/e:archdesc/(' +  \
        '|'.join('e:%s' % field for field in _coll_desc) + '))//exist:match)'
    # - controlaccess match-count
    controlaccess_matches_xpath = 'count(util:expand(%(xq_var)s/e:archdesc/e:controlaccess)//exist:match)'

    origination_name = xmlmap.NodeField('e:archdesc/e:did/e:origination/e:*', Name)
    'origination name, as an instance of :class:`Name`'

    # dao anywhere in the ead, to allow filtering on finding aids with daos
    daos = xmlmap.NodeListField('.//e:dao', DigitalArchivalObject)
    #: count of public dao elements in a record, to support search filtering
    #: "public" is defined as audience external or not set, xlink:href present,
    #: and show not set to none.
    public_dao_count = xmlmap.IntegerField('count(.//e:dao[@xlink:href][not(@xlink:show="none")][not(@audience) or @audience="external"])')

    objects = Manager('/e:ead')
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving FindingAid objects
        in eXist.

        Configured to use */ead* as base search path.
    """

    @property
    def has_digital_content(self):
        'boolean to indicate whether or not this EAD includes public digital content'
        return self.public_dao_count >= 1
        # NOTE: if using partial xml return, requires that public_dao_count is included

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
        for rel_m in self.relatedmaterial_list:
            info.append(rel_m)
        for sep_m in self.separatedmaterial_list:
            info.append(sep_m)
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


    collection_id = xmlmap.StringField('e:archdesc/e:did/e:unitid/@identifier')

    def collection_uri(self):
        # URI to use in RDF for the archival collection, as distinguished
        # from the findingaid document that describes the collection and
        # the materials that it includes.

        if self.collection_id is not None and \
           self.collection_id.startswith('http'):
            # if collection id is a URL, use that
            return self.collection_id

        else:
            # otherwise use findingaid ARK as base for collection URI
            return '%s#collection' % self.eadid.url

    def absolute_eadxml_url(self):
        ''' Generate an absolute url to the xml view for this ead
            for use with external services such as Aeon'''

        current_site = Site.objects.get_current()
        return ''.join([
            'http://',
            current_site.domain.rstrip('/'),
            reverse('fa:eadxml', kwargs={"id":self.eadid.value})
            ])

    def request_materials_url(self):
        ''' Construct the absolute url for use with external services such as Aeon'''

        if not hasattr(settings, 'REQUEST_MATERIALS_URL') or not settings.REQUEST_MATERIALS_URL:
            logger.warn("Request materials url is not configured.")
            return

        base = settings.REQUEST_MATERIALS_URL
        return ''.join([base, self.absolute_eadxml_url()])

    def requestable(self):
        ''' Determines if the EAD is applicable for the electronic request service.'''

        # If the request url is not configured, then the request can't be generated.
        if not hasattr(settings, 'REQUEST_MATERIALS_URL') or not settings.REQUEST_MATERIALS_URL:
            return False

        if not hasattr(settings, 'REQUEST_MATERIALS_REPOS') or not settings.REQUEST_MATERIALS_REPOS:
            return False

        # If the item is in on of the libraries defined, then it should be displayed.
        return any([normalize_whitespace(repo) in settings.REQUEST_MATERIALS_REPOS
                    for repo in self.repository])


class ListTitle(XmlModel):
    # EAD list title - used to retrieve at the title level for better query response
    ROOT_NAMESPACES = {'e': eadmap.EAD_NAMESPACE}
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
    ROOT_NAMESPACES = {'e': eadmap.EAD_NAMESPACE}
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


class LocalComponent(eadmap.Component):
    '''Extend default :class:`eulcore.xmlmap.eadmap.Component` class to add a
    method to detect first file-item in a list.  (Needed for container list display
    in templates).'''
    ROOT_NAMESPACES = {
        'e': eadmap.EAD_NAMESPACE,
    }
    # by local convention, section headers are sibling components with no containers
    preceding_files = xmlmap.NodeListField('preceding-sibling::node()[@level="file"][e:did/e:container]', "self")

    @property
    def first_file_item(self):
        'Boolean: True if this component is the first file item in a series/container list'
        return len(self.did.container) and len(self.preceding_files) == 0


def title_rdf_identifier(src, idno):
    ''''Generate an RDF identifier for a title, based on source and id
    attributes.  Currently supports ISSN, ISBN, and OCLC.'''
    src = src.lower()
    idno = idno.strip()  # remove whitespace, just in case of errors in entry

    if src in ['isbn', 'issn']:  # isbn and issn URNs have same format
        return 'urn:%s:%s' % (src.upper(), idno)
    elif src == 'oclc':
        return 'http://www.worldcat.org/oclc/%s' % idno


class Title(xmlmap.XmlObject):
    '''A title in an EAD document, with access to attributes for type of title,
    render, source, and authfilenumber.
    '''
    ROOT_NAMESPACES = {'e': eadmap.EAD_NAMESPACE}
    ROOT_NAME = 'title'

    type = xmlmap.StringField('@type')
    render = xmlmap.StringField('@render')
    source = xmlmap.StringField('@source')
    authfilenumber = xmlmap.StringField('@authfilenumber')
    value = xmlmap.StringField('.', normalize=True)

    @property
    def rdf_identifier(self):
        ''''RDF identifier for this title, if source and authfilenumber attributes
        are present and can be converted into a URI or URN'''
        return title_rdf_identifier(self.source, self.authfilenumber)


class Series(XmlModel, LocalComponent):
    """
      Top-level (c01) series.

      Customized version of :class:`eulcore.xmlmap.eadmap.Component`
    """

    ROOT_NAMESPACES = {
        'e': eadmap.EAD_NAMESPACE,
        'exist': 'http://exist.sourceforge.net/NS/exist'
    }

    ead = xmlmap.NodeField("ancestor::e:ead", FindingAid)
    ":class:`findingaids.fa.models.FindingAid` access to ancestor EAD element"
    # NOTE: using [1] to get closest ancestor; in case of existdb 'also'
    # return result, possible to have nested ead elements.

    parent = xmlmap.NodeField("parent::node()", "self")

    objects = Manager('//e:c01')
    # NOTE: this element should not be restricted by level=series because eXist full-text indexing
    # is more efficient if the queried element matches the indexed element
    """:class:`eulcore.django.existdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving c01 series objects
        in eXist.

        Configured to use *//c01* as base search path.
    """

    # temporary manual mapping for processinfo, should be incorporated into a release of eulxml
    process_info = xmlmap.NodeField("e:processinfo", eadmap.Section)

    match_count = xmlmap.IntegerField("count(.//exist:match)")
    ":class:`findingaids.fa.models.FindingAid` number of keyword matchs"

    _unittitle_name_xpath = '|'.join('e:did/e:unittitle/e:%s' % t
                                     for t in ['persname', 'corpname', 'geogname'])
    #: tagged name in the unittitle; used for RDFa output
    unittitle_name = xmlmap.NodeField(_unittitle_name_xpath, Name)
    'name in the unittitle, as an instance of :class:`Name`'
    #: list of tagged names in the unittite; used for RDFa output
    unittitle_names = xmlmap.NodeListField(_unittitle_name_xpath, Name)
    'names in the unittitle, as a list of :class:`Name`'

    #: list of titles in the unittitle; used for RDFa output
    unittitle_titles = xmlmap.NodeListField('e:did/e:unittitle/e:title', Title)
    'list of titles in the unittitle, as :class:`Title`'

    #: title of the nearest ancestor series;
    #: used to determine what kind of content this is, for default rdf type
    series_title = xmlmap.StringField('''ancestor::e:c03[@level="subsubseries"]/e:did/e:unittitle
        |ancestor::e:c02[@lavel="subseries"]/e:did/e:unittitle
        |ancestor::e:c01[@level="series"]/e:did/e:unittitle''',
        normalize=True)

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
        if self.process_info:
            fields.append(self.process_info)


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

    @property
    def has_semantic_data(self):
        '''Does this item contains semantic data that should be rendered with
        RDFa?  Currently checks the unittitle for a tagged person, corporate, or
        geographic name or for a title with source and authfilenumber attributes.'''
        # - if there is at least one tagged name in the unittitle
        semantic_tags = [self.unittitle_name]
        # - if there are titles tagged with source/authfilenumber OR titles
        # with a type
        # NOTE: eventually, we will probably want to include all tagged titles,
        # but for now, restrict to titles that have been enhanced in a particular way
        semantic_tags.extend([t for t in self.unittitle_titles
                              if (t.source and t.authfilenumber) or t.type])
        return any(semantic_tags)

    @property
    def contains_correspondence(self):
        'Boolean property indicating if this series containes correspondence.'
        return 'correspondence' in unicode(self.did.unittitle).lower()

    @property
    def rdf_type(self):
        ''''rdf type to use for a semantically-tagged component item'''
        # NOTE: initial implementation for Belfast Group sheets assumes manuscript
        # type; should be refined for other types of content
        rdf_type = None
        if self.unittitle_titles:
            # if type of first title is article, return article
            if self.unittitle_titles[0].type and \
              self.unittitle_titles[0].type.lower() == 'article':
                rdf_type = 'bibo:Article'

            # if two titles and the second has an issn, article in a periodical
            # (TODO: is this close enough for all cases?)
            elif len(self.unittitle_titles) == 2 and self.unittitle_titles[1].source \
              and self.unittitle_titles[1].source.upper() == 'ISSN':
                rdf_type = 'bibo:Article'

            # if title has an isbn, assume it is a book
            # - for now, also assume OCLC source is book (FIXME: is this accurate?)
            elif self.unittitle_titles[0].source \
              and self.unittitle_titles[0].source.upper() in ['ISBN', 'OCLC']:
                rdf_type = 'bibo:Book'

            else:
                rdf_type = self.generic_rdf_type_by_series()

        # if there are no titles but there is a name with a role of creator,
        # the component describes some kind of entity, so set the type
        # based on series
        elif self.unittitle_names and 'dc:creator' in [n.role for n in self.unittitle_names]:
            rdf_type = self.generic_rdf_type_by_series()

        return rdf_type

    def generic_rdf_type_by_series(self):
        '''Calculate a generic RDF type based on the series an item belongs to.
        Using bibo:Document for printed material, bibo:Image for photographs,
        bibo:AudioVisualDocument for audio/visual materials, with a fallback
        of bibo:Manuscript.'''
        if self.series_title:
            series_title = self.series_title.lower()
            # if in a Printed Material series, assume bibo:Document
            # - printed material is usually included in text for series and
            #   subseries names
            if 'printed material' in series_title:
                return 'bibo:Document'

            # if in a Photographs series, use bibo:Image
            elif 'photograph' in series_title:
                return 'bibo:Image'

            # if in an AudioVisual series, use bibo:AudioVisualDocument
            elif 'audiovisual' in series_title or \
              'audio recordings' in series_title or \
              'video recordings' in series_title:
               # audiovisual usually used at top-level, audio/video rec. used for subseries
                return 'bibo:AudioVisualDocument'

        # otherwise, use bibo:Manuscript
        return 'bibo:Manuscript'


    @property
    def rdf_identifier(self):
        # if the item in the unittitle has an rdf identifier, make it available
        # for use in constructing RDFa in the templates

        # for now, assuming that the first title listed is the *thing*
        # in the collection.  If we can generate an id for it (i.e.,
        # it has a source & authfilenumber), use that
        if self.unittitle_titles:
            return self.unittitle_titles[0].rdf_identifier

        # NOTE: previously, was only returning an rdf identifier for a
        # single title
        # for now, only return when these is one single title
        # if len(self.unittitle_titles) == 1 :
            # return self.unittitle_titles[0].rdf_identifier

    @property
    def rdf_mentions(self):
        # names related to the title that should also be related to the collection
        # titles after the first two need to be handled separately here also
        return self.rdf_type is not None and len(self.unittitle_names) \
          or len(self.unittitle_titles) > 1

    @property
    def mention_titles(self):
        # list of secondary titles that should be mentioned

        # if we have a multiple titles with an author, the titles
        # are being treated as a list and should not be exposed
        # (i.e., belfast group sheets)
        if self.unittitle_names and any(n.role for n in self.unittitle_names)  \
          or len(self.unittitle_titles) <= 1:
            return []
        else:
            # return all but the first title
            return list(self.unittitle_titles)[1:]


# override component.c node_class
# subcomponents need to be initialized as Series to get display_label, series list...
# FIXME: look for a a better way to do this kind of XmlObject extension
eadmap.Component._fields['c'].node_class = Series
eadmap.SubordinateComponents._fields['c'].node_class = Series

# override DigitalArchivalObject with local version
eadmap.DescriptiveIdentification._fields['dao_list'].node_class = DigitalArchivalObject
eadmap.Component._fields['dao_list'].node_class = DigitalArchivalObject
eadmap.ArchivalDescription._fields['dao_list'].node_class = DigitalArchivalObject

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


class Index(XmlModel, eadmap.Index):
    """
      EAD Index, with index entries.

      Customized version of :class:`eulcore.xmlmap.eadmap.Index`
    """

    ROOT_NAMESPACES = {
        'e': eadmap.EAD_NAMESPACE,
        'xlink': eadmap.XLINK_NAMESPACE,
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
eadmap.ArchivalDescription._fields['index'].node_class = Index


class FileComponent(XmlModel, eadmap.Component):
    """
    Any EAD component with a level of *file*, with item-level information (box &
    folder contents).
    """

    ROOT_NAMESPACES = {
        'e': eadmap.EAD_NAMESPACE,
        'xlink': eadmap.XLINK_NAMESPACE,
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

    #: count of public daos; same as in :attr:`FindingAid.public_dao_count`
    public_dao_count = xmlmap.IntegerField('count(.//e:dao[@xlink:href][not(@xlink:show="none")][not(@audience) or @audience="external"])')


    # objects = Manager('''(e:ead//e:c01|e:ead//e:c02|e:ead//e:c03|e:ead//e:c04)[@level="file"]''')
    # eXist can query *much* more efficiently on generic paths
    objects = Manager('''//*[@level="file"]''')
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
    note = models.CharField(
        max_length=400, blank=True,
        help_text="Optional: Enter the reason this document is being deleted. " +
                  "These comments will be displayed to anyone who had the finding " +
                  "aid bookmarked and returns after it is gone.")

    class Meta:
        verbose_name = 'Deleted Record'

    def __unicode__(self):
        return self.eadid


class Archive(models.Model):
    '''Model to define Archives associated with EAD documents, for use with
    admin user permissions and to identify subversion repositories where
    content will be published from.'''
    label = models.CharField(max_length=10,
        help_text='Short label to identify an archive')
    name = models.CharField(max_length=255,
        help_text='repository name (subarea) in EAD to identify finding aids associated with this archive')
    svn = models.URLField('Subversion Repository',
        help_text='URL to subversion repository containing EAD for this archive')
    slug = models.SlugField(help_text='''shorthand id
        (auto-generated from label; do not modify after initial archive definition)''')

    def __unicode__(self):
        return self.label

    @property
    def svn_local_path(self):
        return os.path.join(settings.SVN_WORKING_DIR, self.slug)
