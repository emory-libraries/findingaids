from os import path
from glob import glob
import re
from types import ListType
from django.test import Client, TestCase
from django.conf import settings
from eulcore.xmlmap  import load_xmlobject_from_file
from eulcore.django.existdb.db import ExistDB
from findingaids.fa.models import FindingAid, Series, Subseries, Subsubseries
from findingaids.fa.views import _series_url, _subseries_links

class FindingAidTestCase(TestCase):
    # test finding aid model (customization of eulcore xmlmap ead object)
    FIXTURES = ['leverette135.xml',  # simple finding aid (no series/subseries), origination is a person name
                'abbey244.xml',	     # finding aid with series (no subseries), origination is a corporate name
                'raoul548.xml',	     # finding aid with series & subseries, origination is a family name
                'bailey807.xml',     # finding aid with series, no origination
                'adams465.xml'
                ]
    
    def setUp(self):
        self.findingaid = dict()
        for file in self.FIXTURES:
            filebase = file.split('.')[0]
            self.findingaid[filebase] = load_xmlobject_from_file(path.join(path.dirname(path.abspath(__file__)) ,
                                  'fixtures', file), FindingAid)


    def test_init(self):
        for file, fa in self.findingaid.iteritems():
            self.assert_(isinstance(fa, FindingAid))

        # TODO: test queryset/manager? (current implementation will change when eulcore existdb model is created)

    def test_custom_fields(self):
        # list title variants
        #  - origination, person name
        self.assertEqual("Leverette, Fannie Lee.", self.findingaid['leverette135'].list_title)
        self.assertEqual("L", self.findingaid['leverette135'].first_letter)
        #  - origination, corporate name
        self.assertEqual("Abbey Theatre.", self.findingaid['abbey244'].list_title)
        self.assertEqual("A", self.findingaid['abbey244'].first_letter)
        #  - origination, family name
        self.assertEqual("Raoul family.", self.findingaid['raoul548'].list_title)
        self.assertEqual("R", self.findingaid['raoul548'].first_letter)
        #  - no origination - list title falls back to unit title
        self.assertEqual("Bailey and Thurman families papers, circa 1882-1995",
                         self.findingaid['bailey807'].list_title)
        self.assertEqual("B", self.findingaid['bailey807'].first_letter)

    # FIXME/TODO: test admin info, collection description ?  (tested in view_series to some extent)

    def test_series_info(self):
        info = self.findingaid['raoul548'].dsc.c[0].series_info()
        self.assert_(isinstance(info, ListType))
        self.assertEqual("Scope and Content Note", info[0].head)
        self.assertEqual("Arrangement Note", info[1].head)

        # FIXME/TODO: test other possible fields not present in this series?


    def test_series_displaylabel(self):
        self.assertEqual("Series 1: Letters and personal papers, 1865-1982",
                self.findingaid['raoul548'].dsc.c[0].display_label())
        # no unitid
        self.assertEqual("Financial and legal papers, 1890-1970",
                self.findingaid['raoul548'].dsc.c[2].display_label())



class FaViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.db = ExistDB()

        #traverse exist_fixtures and load all xml files
        module_path = path.split(__file__)[0]
        fixtures_glob = path.join(module_path, 'fixtures', '*.xml')
        for fixture in glob(fixtures_glob):
            fname = path.split(fixture)[-1]
            exist_fname = path.join(settings.EXISTDB_ROOT_COLLECTION, fname)
            self.db.load(open(fixture), exist_fname, True)

    def tearDown(self):
        pass
        
    def test_title_letter_list(self):
        response = self.client.get('/titles')
        self.assertEquals(response.status_code, 200)

        response = self.client.get('/titles/')
        self.assertEquals(response.status_code, 200)

        # first letters from 4 test documents
        self.assertContains(response, 'href="/titles/A"')
        self.assertContains(response, 'href="/titles/B"')
        self.assertContains(response, 'href="/titles/L"')
        self.assertContains(response, 'href="/titles/R"')
        # should not include first letters not present in the data
        self.assertContains(response, 'href="/titles/Z"', 0)

    def test_titles_by_letter(self):
        response = self.client.get('/titles/A')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'href="/documents/abbey244')
        self.assertContains(response, '<p class="abstract">Collection of play scripts')
        self.assertContains(response, '2 finding aids found')
        # test pagination ?
        
        # test current letter
        # TODO regex test?  remove whitespace to test better?
        self.assertContains(response, "<li class='active'>")

        # no finding aids
        response = self.client.get('/titles/Z')
        self.assertContains(response, '<div>No finding aids found.</div>')

    def test_view_notfound(self):
        response = self.client.get('/documents/nonexistent')
        self.assertEquals(response.status_code, 404)

    def test_view_simple(self):
        response = self.client.get('/documents/leverette135')
        self.assertEquals(response.status_code, 200)
        # title
        self.assert_(re.search('|<h1>Fannie Lee Leverette scrapbooks,\w+circa 1900-1948</h1>|',
                    response.content))
        # descriptive summary content
        self.assert_(re.search('|Creator:.*Leverette, Fannie Lee|', response.content))
        self.assert_(re.search('|Title:.*Fannie Lee Leverette scrapbooks,circa 1900-1948|', response.content))
        self.assert_(re.search('|Call Number:.*Manuscript Collection\w+No.135|', response.content))
        self.assert_(re.search('|Extent:.*1 microfilm reel\w+MF|', response.content))
        self.assert_(re.search('|Abstract:.*Microfilm copy of four scapbooks|', response.content))
        self.assert_(re.search('|Language:.*Materials entirely in\w+English|', response.content))
        self.assert_('Location:' not in response.content)       # not in xml, should not display

        # admin info
        self.assert_(re.search('|Restrictions on Access.*Unrestricted access.|', response.content))
        self.assert_(re.search('|Terms Govererning Use and Reproduction.*All requests subject to limitations.|',
                    response.content))
        self.assert_(re.search('|Source.*Loaned for reproduction, 1978.|', response.content))
        self.assert_(re.search('|Citation.*[after identification of item(s)], Fannie Lee Leverette scapbooks.|',
                    response.content))
        self.assert_('Related Materials' not in response.content)       # not in xml, should not display

        # collection description
        self.assert_(re.search('|Biographical Note.*born in Eatonton, Putnam County, Georgia|',
                    response.content))
        self.assert_(re.search('|Scope and Content Note.*collection consists of|',
                    response.content))

        # controlaccess
        self.assert_(re.search('|<h2>.*Selected Search Terms.*</h2>|',
                    response.content))
        self.assert_(re.search('|Personal Names\.*Collins, M\.D\..*Farley, James A\.|',
                    response.content))
        self.assert_(re.search('|Topical Terms.*African Americans--Georgia--Eatonton\..*Education--Georgia\.|',
                    response.content))
        self.assert_(re.search('|Geographic Names.*Augusta \(Ga\.\).*Eatonton \(Ga\.\)|',
                    response.content))
        self.assert_(re.search('|Form\\Genre Terms.*Photographs\..*Scrapbooks\.|',
                    response.content))
        self.assert_(re.search('|Occupation.*Educator\..*Journalist|',
                    response.content))

        # dsc
        self.assert_(re.search('|<h2>.*Container List.*</h2>|', response.content))
        self.assert_(re.search('|Scrapbook 1.*Box.*Folder.*Content.*MF1|', response.content))
        self.assert_(re.search('|MF1.*1.*Photo and clippings re Fannie Lee Leverette|', response.content))
        self.assert_(re.search('|MF1.*4.*Family and personal photos|', response.content))

    def test_view_series(self):
        response = self.client.get('/documents/abbey244')
        self.assertEquals(response.status_code, 200)

        # admin info fields not present in leverette
        self.assert_(re.search('|Related Materials in This Repository.*William Butler Yeats collection|',
            response.content))
        self.assert_(re.search('|Historical Note.*Abbey Theatre, organized in 1904|',
            response.content))
        self.assert_(re.search('|Arrangement Note.*Organized into three series|',
            response.content))

        # series instead of container list
        self.assert_(re.search('|<h2>.*Description of Series.*</h2>|', response.content))
        self.assert_(re.search('|<a href.*>Series 1: Plays</a>|', response.content))
        self.assert_(re.search('|<a href.*>Series 2: Programs.*</a>|', response.content))
        self.assert_(re.search('|<a href.*>Series 3: Other material, 1935-1941.*</a>|', response.content))

    def test_view_subseries(self):
        response = self.client.get('/documents/raoul548')
        self.assertEquals(response.status_code, 200)

        # admin info fields not present in previous fixtures
        self.assert_(re.search('|Related Materials in Other Repositories.*original Wadley diaries|',
            response.content))        

        # collection description - multiple paragraphs
        self.assert_(re.search('|Biographical Note.*centered in Georgia.*eleven children.*moved to New York|',
            response.content))      # text from first 3 paragraphs
        self.assert_(re.search('|Scope and Content Note.*contain letters, journals.*arranged in four series.*document the life|',
            response.content))

        # series instead of container list
        self.assert_(re.search('|<h2>.*Description of Series.*</h2>|', response.content))
        self.assert_(re.search('|<a href.*>Series 1: Letters and personal papers.*</a>|', response.content))
        self.assert_(re.search('|<a href.*>Subseries 1.1: William Greene Raoul paper.*</a>|', response.content))
        self.assert_(re.search('|<a href.*>Subseries 1.2: Mary Wadley Raoul papers.*</a>|', response.content))
        self.assert_(re.search('|<a href.*>Subseries 1.13: Normal Raoul papers.*</a>|', response.content))
        self.assert_(re.search('|<a href.*>Series 2: Photographs, circa 1850-1960</a>|', response.content))
        self.assert_(re.search('|<a href.*>Series 4: Miscellaneous, 1881-1982</a>|', response.content))


    def test_view_nodsc(self):
        response = self.client.get('/documents/adams465')
        self.assertEquals(response.status_code, 200)

        # record with no dsc - no container list or series
        self.assert_('Container List' not in response.content)
        self.assert_('Description of Series' not in response.content)

        # FIXME: test also not listed in top-level table of contents?

    def test__series_url(self):
        self.assertEqual('/documents/docid/s1', _series_url('docid', 's1'))
        self.assertEqual('/documents/docid/s1/s1.2', _series_url('docid', 's1', 's1.2'))
        self.assertEqual('/documents/docid/s3/s3.5/s3.5a', _series_url('docid', 's3', 's3.5', 's3.5a'))

    def test__subseries_links__dsc(self):
        # subseries links for a top-level series that has subseries
        fa = FindingAid.objects.get(eadid='raoul548')
        links = _subseries_links(fa.dsc, url_ids=[fa.eadid])
        
        self.assert_("Series 1: Letters and personal papers" in links[0])
        self.assert_("href='/documents/raoul548/raoul548_1003223'" in links[0])
        # nested list for subseries
        self.assert_(isinstance(links[1], ListType))
        self.assert_("Subseries 1.1: William Greene" in links[1][0])
        self.assert_("href='/documents/raoul548/raoul548_1003223/raoul548_100355'" in links[1][0])

        # second-to-last entry - series 4
        self.assert_("Series 4: Misc" in links[-2])
        self.assert_("href='/documents/raoul548/raoul548_s4'" in links[-2])
        # last entry - series 4 subseries
        self.assert_(isinstance(links[-1], ListType))
        self.assert_("Subseries 4.1:" in links[-1][0])
        # series 4.1 sub-subseries
        self.assert_(isinstance(links[-1][1], ListType))
        self.assert_("Subseries 4.1a:" in links[-1][1][0])
        


    def test__subseries_links(self):
        # subseries links for a top-level series that has subseries
        series = Series.objects.also('ead__eadid').get(id='raoul548_1003223')
        links = _subseries_links(series)
        
        self.assertEqual(13, len(links))  # raoul series has subseries 1-13
        self.assert_("href='/documents/raoul548/raoul548_1003223/raoul548_100904'" in links[2])
        self.assert_('Subseries 1.1: William Greene' in links[0])
        self.assert_("href='/documents/raoul548/raoul548_1003223/raoul548_100355'" in links[0])
        self.assert_('Subseries 1.2: Mary Wadley' in links[1])
        self.assert_("href='/documents/raoul548/raoul548_1003223/raoul548_100529'" in links[1])
        self.assert_('Subseries 1.3: Sarah Lois' in links[2])
        self.assert_("href='/documents/raoul548/raoul548_1003223/raoul548_100904'" in links[2])
        self.assert_('Subseries 1.13: Norman Raoul' in links[-1])
        self.assert_("href='/documents/raoul548/raoul548_1003223/raoul548_1003222'" in links[-1])

        series = Series.objects.get(id='raoul548_1003223')
        # should get exception when top-level ead id is not available
        self.assertRaises(Exception, _subseries_links, series)


    def test__subseries_links_nested(self):
        # subseries links for a top-level series that has subseries with sub-subseries (nested list)
        series = Series.objects.also('ead__eadid').get(id='raoul548_s4')
        links = _subseries_links(series)
        
        self.assert_("Subseries 4.1: Misc" in links[0])
        self.assert_("href='/documents/raoul548/raoul548_s4/raoul548_4.1'" in links[0])
        self.assert_(isinstance(links[1], ListType))
        self.assert_("Subseries 4.1a: Genealogy" in links[1][0])
        self.assert_("href='/documents/raoul548/raoul548_s4/raoul548_4.1/raoul548_4.1a'" in links[1][0])
        self.assert_("Subseries 4.1b: Genealogy part 2" in links[1][1])
        self.assert_("href='/documents/raoul548/raoul548_s4/raoul548_4.1/raoul548_4.1b'" in links[1][1])
        

    def test__subseries_links_c02(self):
        # subseries links when not starting at c01 level
        series = Subseries.objects.also('ead__eadid', 'series__id').get(id='raoul548_4.1')
        links = _subseries_links(series)

        self.assertEqual(2, len(links))     # test doc has two c03 subseries
        self.assert_("Subseries 4.1a: Genealogy" in links[0])
        self.assert_("href='/documents/raoul548/raoul548_s4/raoul548_4.1/raoul548_4.1a'" in links[0])
        self.assert_("Subseries 4.1b: Genealogy part 2" in links[1])
        self.assert_("href='/documents/raoul548/raoul548_s4/raoul548_4.1/raoul548_4.1b'" in links[1])

        # c02 retrieved without parent c01 id should get an exception
        series = Subseries.objects.also('ead__eadid').get(id='raoul548_4.1')        
        self.assertRaises(Exception, _subseries_links, series)

    def test__subseries_links_c03(self):
        # c03 retrieved without parent c01 id should get an exception
        series = Subsubseries.objects.also('ead__eadid').get(id='raoul548_4.1a')
        self.assertRaises(Exception, _subseries_links, series)

        # c03 with series but not subseries id - still exception
        series = Subsubseries.objects.also('ead__eadid', 'series__id').get(id='raoul548_4.1a')
        self.assertRaises(Exception, _subseries_links, series)

        # all required parent ids - no exception
        series = Subsubseries.objects.also('ead__eadid', 'series__id', 'subseries__id').get(id='raoul548_4.1a')
        self.assertEqual([], _subseries_links(series))




