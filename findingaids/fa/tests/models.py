# file findingaids/fa/tests/models.py
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

from os import path
from types import ListType
from mock import patch

from django.conf import settings
from django.test import TestCase as DjangoTestCase
from django.test.utils import override_settings

from eulxml.xmlmap import load_xmlobject_from_file, load_xmlobject_from_string
from eulxml.xmlmap.eadmap import EAD_NAMESPACE
from eulexistdb.testutil import TestCase

from findingaids.fa.models import FindingAid, LocalComponent, EadRepository, \
    Series, Title, PhysicalDescription
# from findingaids.fa.utils import pages_to_show, ead_lastmodified, \
    # collection_lastmodified


## unit tests for model objects in findingaids.fa

exist_fixture_path = path.join(path.dirname(path.abspath(__file__)), 'fixtures')
exist_index_path = path.join(path.dirname(path.abspath(__file__)), '..', '..', 'exist_index.xconf')


class FindingAidTestCase(DjangoTestCase):
    # test finding aid model (customization of eulcore xmlmap ead object)
    FIXTURES = ['leverette135.xml',  # simple finding aid (no series/subseries), origination is a person name
                'abbey244.xml',      # finding aid with series (no subseries), origination is a corporate name
                'raoul548.xml',      # finding aid with series & subseries, origination is a family name
                'bailey807.xml',     # finding aid with series, no origination
                'adams465.xml',
                'pomerantz890.xml'  # finding aid with multiple subareas
                ]

    def setUp(self):
        self.findingaid = dict()
        for file in self.FIXTURES:
            filebase = file.split('.')[0]
            self.findingaid[filebase] = load_xmlobject_from_file(path.join(exist_fixture_path,
                                  file), FindingAid)

    def test_init(self):
        for file, fa in self.findingaid.iteritems():
            self.assert_(isinstance(fa, FindingAid))

    def test_custom_fields(self):
        # list title variants
        # NOTE: list_title is now a NodeField; calling __unicode__ explicitly to do a string compare
        #  - origination, person name
        self.assertEqual("Leverette, Fannie Lee.", self.findingaid['leverette135'].list_title.__unicode__())
        self.assertEqual("L", self.findingaid['leverette135'].first_letter)
        #  - origination, corporate name
        self.assertEqual("Abbey Theatre.", self.findingaid['abbey244'].list_title.__unicode__())
        self.assertEqual("A", self.findingaid['abbey244'].first_letter)
        #  - origination, family name
        self.assertEqual("Raoul family.", self.findingaid['raoul548'].list_title.__unicode__())
        self.assertEqual("R", self.findingaid['raoul548'].first_letter)
        #  - no origination - list title falls back to unit title
        self.assertEqual("Bailey and Thurman families papers, circa 1882-1995",
                         self.findingaid['bailey807'].list_title.__unicode__())
        self.assertEqual("B", self.findingaid['bailey807'].first_letter)

        # dc_subjects
        self.assert_(u'Irish drama--20th century.' in self.findingaid['abbey244'].dc_subjects)
        self.assert_(u'Theater--Ireland--20th century.' in self.findingaid['abbey244'].dc_subjects)
        self.assert_(u'Dublin (Ireland)' in self.findingaid['abbey244'].dc_subjects)
        # dc_contributors
        self.assert_(u'Bailey, I. G. (Issac George), 1847-1914.' in self.findingaid['bailey807'].dc_contributors)
        self.assert_(u'Bailey, Susie E., d. 1948.' in self.findingaid['bailey807'].dc_contributors)
        self.assert_(u'Thurman, Howard, 1900-1981.' in self.findingaid['bailey807'].dc_contributors)
        self.assert_(u'Thurman, Sue Bailey.' in self.findingaid['bailey807'].dc_contributors)

    def test_has_digital_content(self):
        # abbey has a dao, but audience is internal
        self.assertFalse(self.findingaid['abbey244'].has_digital_content)
        # no dao in adams
        self.assertFalse(self.findingaid['adams465'].has_digital_content)
        # daos have been added to leverette fixture
        self.assertTrue(self.findingaid['leverette135'].has_digital_content)

    def test_stored_offsite(self):
        self.assertFalse(self.findingaid['abbey244'].stored_offsite)
        self.assertTrue(self.findingaid['pomerantz890'].stored_offsite)

    def test_series_info(self):
        info = self.findingaid['raoul548'].dsc.c[0].series_info()
        self.assert_(isinstance(info, ListType))
        self.assertEqual("Scope and Content Note", unicode(info[0].head))
        self.assertEqual("Arrangement Note", unicode(info[1].head))

        # series info problem when scopecontent is missing a <head>; contains use restriction
        info = self.findingaid['raoul548'].dsc.c[-1].c[-1].series_info()
        self.assert_(isinstance(info, ListType))
        self.assert_("contains all materials related to " in
            info[0].content[0].__unicode__())  # scopecontent with no head
        self.assertEqual("Arrangement Note", unicode(info[1].head))
        self.assertEqual("Terms Governing Use and Reproduction", unicode(info[2].head))
        self.assertEqual("Restrictions on Access", unicode(info[3].head))

    def test_series_displaylabel(self):
        self.assertEqual("Series 1: Letters and personal papers, 1865-1982",
                self.findingaid['raoul548'].dsc.c[0].display_label())
        # no unitid
        self.assertEqual("Financial and legal papers, 1890-1970",
                self.findingaid['raoul548'].dsc.c[2].display_label())

    def test_dc_fields(self):
        fields = self.findingaid['abbey244'].dc_fields()

        self.assert_("Abbey Theatre collection, 1921-1995" in [title.__unicode__() for title in fields["title"]])
        self.assert_("Abbey Theatre." in fields["creator"])
        self.assert_("Emory University" in fields["publisher"])
        self.assert_("2002-02-24" in fields["date"])
        self.assert_("eng" in fields["language"])
        self.assert_("Irish drama--20th century." in fields["subject"])
        self.assert_("Theater--Ireland--20th century." in fields["subject"])
        self.assert_("Dublin (Ireland)" in fields["subject"])
        self.assert_("http://pidtest.library.emory.edu/ark:/25593/1fx" in fields["identifier"])

        fields = self.findingaid['bailey807'].dc_fields()
        self.assert_("Bailey, I. G. (Issac George), 1847-1914." in fields["contributor"])
        self.assert_("Bailey, Susie E., d. 1948." in fields["contributor"])
        self.assert_("Thurman, Howard, 1900-1981." in fields["contributor"])
        self.assert_("Thurman, Sue Bailey." in fields["contributor"])

    def test_local_component(self):
        # local component with custom property - first_file_item
        self.assert_(isinstance(self.findingaid['abbey244'].dsc.c[0], LocalComponent))
        self.assert_(isinstance(self.findingaid['abbey244'].dsc.c[0].c[0], LocalComponent))
        # abbey244 series 1 - no section headings, first c should be first file
        self.assertTrue(self.findingaid['abbey244'].dsc.c[0].c[0].first_file_item)
        self.assertFalse(self.findingaid['abbey244'].dsc.c[0].c[1].first_file_item)
        self.assertFalse(self.findingaid['abbey244'].dsc.c[0].c[-1].first_file_item)
        # raoul548 series 1.1 - first item is a section, second item should be first file
        self.assertFalse(self.findingaid['raoul548'].dsc.c[0].c[0].c[0].first_file_item)
        self.assertTrue(self.findingaid['raoul548'].dsc.c[0].c[0].c[1].first_file_item)

    def test_absolute_eadxml_url(self):
        # test against current site domain
        url = self.findingaid['abbey244'].absolute_eadxml_url()
        self.assert_(self.findingaid['abbey244'].eadid.value in url,
            'URL should contain the EAD ID for this current document.')

    @override_settings(REQUEST_MATERIALS_URL='http://example.com')
    def test_requestable(self):
        fa = self.findingaid['abbey244']
        fa2 = self.findingaid['bailey807']
        fa3 = self.findingaid['pomerantz890'] # EAD with multiple subareas

        with override_settings(REQUEST_MATERIALS_REPOS = [
            'Manuscript, Archives, and Rare Book Library',
            'Emory University Archives'
            ]):
            self.assertTrue(fa.requestable(),"EAD from Marbl should be able to be requested.")

        # Fail if the REQUEST_MATERIALS_URL is empty
        with override_settings(REQUEST_MATERIALS_URL = ''):
            self.assertFalse(fa.requestable(),"Cannot request EAD if the REQUEST_MATERIALS_URL is not set.")

        # Fail if the REQUEST_MATERIALS_REPOS is empty
        with override_settings(REQUEST_MATERIALS_REPOS = ''):
            self.assertFalse(fa.requestable(),"Cannot request EAD if the REQUEST_MATERIALS_REPOS is not set.")

        # Fail if the requested EAD repo is not set in REQUEST_MATERIALS_REPOS
        with override_settings(REQUEST_MATERIALS_REPOS = [
            'Manuscript, Archives, and Rare Book Library'
            ]):
            self.assertFalse(fa2.requestable(),"EAD from University Archives (not set) shouldn't be able to be requested.")

        # Multiple subareas per one EAD
        with override_settings(REQUEST_MATERIALS_REPOS = [
            'Pitts Theology Library'
            ]):
            self.assertTrue(fa3.requestable(),"Even if there are multiple subareas, an EAD from the set repos should be able to be requested.")

    @override_settings(REQUEST_MATERIALS_URL='http://example.com')
    def test_request_materials_url(self):
        fa = self.findingaid['abbey244']
        self.assert_(fa.request_materials_url())

        del settings.REQUEST_MATERIALS_URL
        self.assertFalse(fa.request_materials_url(),'Cannot return a request materials url if the setting is None')



class EadRepositoryTestCase(TestCase):
    exist_fixtures = {'files': [path.join(exist_fixture_path, 'pomerantz890.xml')] }

    def test_distinct(self):
        repos = EadRepository.distinct()
        # should be a distinct, space-normalized list of subareas
        self.assert_('Pitts Theology Library' in repos)
        self.assert_('Manuscript, Archives, and Rare Book Library' in repos)


class SeriesTestCase(DjangoTestCase):

    # plain file item with no semantic tags
    c1 = load_xmlobject_from_string('''<c02 xmlns="%s" level="file">
          <did>
            <container type="box">1</container>
            <container type="folder">1</container>
            <unittitle>Acey, J. Earl and Port Scott, July 10, 1991. [Cassette
                  available]</unittitle>
          </did>
         </c02>''' % EAD_NAMESPACE, Series)
    # simple tagged person name in the unittitle
    c2 = load_xmlobject_from_string('''<c02 xmlns="%s" level="file">
          <did>
            <container type="box">1</container>
            <container type="folder">1</container>
            <unittitle><persname>Acey, J. Earl</persname> and Port Scott, July 10, 1991. [Cassette
                  available]</unittitle>
          </did>
        </c02>''' % EAD_NAMESPACE, Series)
    # tagged title with source & authfilenumber
    c3 = load_xmlobject_from_string('''<c02 xmlns="%s" level="file">
        <did>
          <container type="box">10</container>
          <container type="folder">24</container>
          <unittitle>
            <title type="scripts" source="OCLC" authfilenumber="434083314">Bayou Legend</title>, notes</unittitle>
        </did>
    </c02>''' % EAD_NAMESPACE, Series)
    # issn title
    c4 = load_xmlobject_from_string('''<c02 xmlns="%s" level="file">
        <did>
          <container type="box">19</container>
          <container type="folder">3</container>
          <unittitle><title render="doublequote" type="article">Who Has Seen the Wind?</title> <title source="ISSN" authfilenumber="2163-6206">New York Amsterdam News</title>, National Scene Magazine Supplement, November-December 1976</unittitle>
        </did></c02>''' % EAD_NAMESPACE, Series)

    c5 = load_xmlobject_from_string('''<c02 xmlns="%s" level="file">
    <did>
        <container type="box">60</container>
        <container type="folder">3</container>
        <unittitle>
            <persname authfilenumber="109557338" role="dc:creator" source="viaf">Heaney, Seamus</persname>,
            <date normal="1965-04-27">April 27, 1965</date>:
            <title render="doublequote">Boy Driving his Father to Confession</title>,
            <title render="doublequote">To A Wine Jar</title>,
            <title render="doublequote">On Hogarth's Engraving 'Pit Ticket for the Royal Sport'</title>
        </unittitle>
    </did>
    </c02>''' % EAD_NAMESPACE, Series)

    def test_has_semantic_data(self):
        self.assertFalse(self.c1.has_semantic_data)
        self.assertTrue(self.c2.has_semantic_data)
        self.assertTrue(self.c3.has_semantic_data)
        self.assertTrue(self.c4.has_semantic_data)
        self.assertTrue(self.c5.has_semantic_data)

    def test_rdf_type(self):
        # not enough information to determine type
        self.assertEqual(None, self.c1.rdf_type)
        # infer book, article, etc from title attributes
        self.assertEqual('bibo:Book', self.c3.rdf_type)
        self.assertEqual('bibo:Article', self.c4.rdf_type)

        # type inferred based on series; requires access to series, so load from fixtures
        # - bailey findingaid contains printed material, photographs, and audiovisual
        bailey = load_xmlobject_from_file(path.join(exist_fixture_path, 'bailey807.xml'),
            FindingAid)

        # patch in unittitles so it looks as though items have semantic data
        with patch('findingaids.fa.models.Series.unittitle_titles', new=[Title()]):

            # series 4 is printed material
            self.assertEqual('bibo:Document', bailey.dsc.c[3].c[0].rdf_type,
                'items in printed materials series should default to document type')

            # series 5 is photographs
            self.assertEqual('bibo:Image', bailey.dsc.c[4].c[0].rdf_type,
                'items in photograph series should default to image type')

            # series 9 is audiovisual
            self.assertEqual('bibo:AudioVisualDocument', bailey.dsc.c[8].c[0].rdf_type,
                'items in audiovisual series should default to audiovisualdocument type')

            # fallback type is manuscript
            self.assertEqual('bibo:Manuscript', bailey.dsc.c[0].c[0].rdf_type,
                'items in photograph series should default to image type')


class PhysicalDescriptionTestCase(DjangoTestCase):

    # multiple extents with separating text
    physdesc1 = load_xmlobject_from_string('''<physdesc xmlns="%s" encodinganalog="300"><extent>5.25 linear ft.</extent>
    <extent> (7 boxes)</extent>,
    <extent>2 bound volumes (BV)</extent>, and
    <extent>11 oversized papers (OP)</extent></physdesc>''' % EAD_NAMESPACE, PhysicalDescription)

    # extents with only space, no punctuation
    physdesc2 = load_xmlobject_from_string('''<physdesc xmlns="%s" encodinganalog="300"><extent>4 linear ft.</extent>
        <extent>(8 boxes)</extent></physdesc>'''  % EAD_NAMESPACE, PhysicalDescription)
    # extents with no space, no punctuation
    physdesc3 = load_xmlobject_from_string('''<physdesc xmlns="%s" encodinganalog="300"><extent>4 linear ft.</extent><extent>(8 boxes)</extent></physdesc>'''  % EAD_NAMESPACE, PhysicalDescription)

    def test_unicode(self):
        self.assertEqual(u'5.25 linear ft. (7 boxes), 2 bound volumes (BV), and 11 oversized papers (OP)',
            unicode(self.physdesc1))

        # should have a space between extents, whether or not it is present in the xml
        self.assertEqual(u'4 linear ft. (8 boxes)', unicode(self.physdesc2))
        self.assertEqual(u'4 linear ft. (8 boxes)', unicode(self.physdesc3))