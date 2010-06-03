from datetime import datetime
from os import path
import re
from types import ListType
from django.http import Http404
from django.test import Client, TestCase as DjangoTestCase
from eulcore.xmlmap  import load_xmlobject_from_file
from eulcore.django.existdb.db import ExistDB
from eulcore.django.test import TestCase
from findingaids.fa.models import FindingAid, Series, Subseries, Subsubseries
from findingaids.fa.views import _series_url, _subseries_links, _series_anchor, \
	_ead_lastmodified, _ead_etag

exist_fixture_path = path.join(path.dirname(path.abspath(__file__)), 'fixtures')
exist_index_path = path.join(path.dirname(path.abspath(__file__)), '..', 'exist_index.xconf')

class FindingAidTestCase(DjangoTestCase):
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
            self.findingaid[filebase] = load_xmlobject_from_file(path.join(exist_fixture_path,
                                  file), FindingAid)


    def test_init(self):
        for file, fa in self.findingaid.iteritems():
            self.assert_(isinstance(fa, FindingAid))

        # TODO: test queryset/manager? (current implementation will change when eulcore existdb model is created)

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

    # FIXME/TODO: test admin info, collection description ?  (tested in view_series to some extent)

    def test_series_info(self):
        info = self.findingaid['raoul548'].dsc.c[0].series_info()
        self.assert_(isinstance(info, ListType))
        self.assertEqual("Scope and Content Note", info[0].head)
        self.assertEqual("Arrangement Note", info[1].head)

        # FIXME/TODO: test other possible fields not present in this series?

        # series info problem when scopecontent is missing a <head>; contains use restriction
        info = self.findingaid['raoul548'].dsc.c[-1].c[-1].series_info()
        self.assert_(isinstance(info, ListType))
        self.assert_("contains all materials related to " in info[0].content[0].__unicode__()) # scopecontent with no head
        self.assertEqual("Arrangement Note", info[1].head)
        self.assertEqual("Terms Governing Use and Reproduction", info[2].head)
        self.assertEqual("Restrictions on Access", info[3].head)

    def test_series_displaylabel(self):
        self.assertEqual("Series 1: Letters and personal papers, 1865-1982",
                self.findingaid['raoul548'].dsc.c[0].display_label())
        # no unitid
        self.assertEqual("Financial and legal papers, 1890-1970",
                self.findingaid['raoul548'].dsc.c[2].display_label())



class FaViewsTest(TestCase):
    exist_fixtures = {'directory' : exist_fixture_path }
    # NOTE: views that require full-text search tested separately below for response-time reasons

    def setUp(self):
        self.client = Client()
        self.db = ExistDB()

    def tearDown(self):
        pass
     
    def test_title_letter_list(self):
        response = self.client.get('/titles')
        self.assertEquals(response.status_code, 301)    # redirect to titles/

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
        self.assertPattern("<a *class='current'[^>]*>A<", response.content)

        # format_ead
        response = self.client.get('/titles/P')
        self.assertPattern(r'''Sweet Auburn</[-A-Za-z]+> research files''', response.content) # title
        self.assertPattern(r'''book,\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn:''', response.content) # abstract

        # no finding aids
        response = self.client.get('/titles/Z')
        self.assertPattern('<div>No finding aids found for .*Z.*</div>', response.content)

    def test_listview(self):
        response = self.client.get('/titles/B')

        # finding aid with no origination - unit title used as browse title & link   
        # - unit title should only be displayed once
        self.assertContains(response, 'Bailey and Thurman families papers', 1)
        
        # Additional case for doubled title problem -title with formatting
        response = self.client.get('/titles/P')
        self.assertContains(response, 'Pitts v. Freeman', 2) # Title and abstract
        self.assertPattern(r'''Pitts v. Freeman</[-A-Za-z]+> school''', response.content) #title within unittitle
    

# view finding aid main page

    def test_view_notfound(self):
        response = self.client.get('/documents/nonexistent')
        self.assertEquals(response.status_code, 404)

    def test_view_simple(self):
        response = self.client.get('/documents/leverette135')
        self.assertEquals(response.status_code, 200)
        # title
        self.assertPattern('<h1[^>]*>.*Fannie Lee Leverette scrapbooks', response.content)
        self.assertContains(response, 'circa 1900-1948</h1>')
        # descriptive summary content
        self.assertPattern('Creator:.*Leverette, Fannie Lee', response.content,
            "descriptive summary - creator")
        self.assertPattern('Title:.*Fannie Lee Leverette scrapbooks,circa 1900-1948',
            response.content, "descriptive summary - title")
        self.assertPattern('Call Number:.*Manuscript Collection.+No.135', response.content,
            "descriptive summary - call number")
        self.assertPattern('Extent:.*1 microfilm reel.+MF', response.content,
            "descriptive summary - extent")
        self.assertPattern('Abstract:.*Microfilm copy of four scrapbooks', response.content,
            "descriptive summary - abstract")
        self.assertPattern('Language:.*Materials entirely in.+English', response.content,
            "descriptive summary - language")
        self.assertNotContains(response, 'Location:')       # not in xml, should not display

        # admin info
        self.assertPattern('Restrictions on Access.*Unrestricted access.', response.content,
            "admin info - access restrictions")
        self.assertPattern('Terms Governing Use and Reproduction.*All requests subject to limitations.',
            response.content, "admin info - use restrictions")
        self.assertPattern('Source.*Loaned for reproduction, 1978.', response.content,
            "admin info - source")
        self.assertPattern('Citation.*\[after identification of item\(s\)\], Fannie Lee Leverette scrapbooks.',
                    response.content, "admin info - preferred citation")
        self.assertNotContains(response, 'Related Materials')       # not in xml, should not display

        # collection description
        self.assertPattern('Biographical Note.*born in Eatonton, Putnam County, Georgia',
                    response.content, "collection description - biography")
        self.assertPattern('Scope and Content Note.*collection consists of',
                    response.content, "collection description - scope & content")

        # controlaccess
        self.assertPattern('<h2>.*Selected Search Terms.*</h2>', response.content,
            "control access heading")
        self.assertPattern('<h3>Personal Names</h3>.*Collins, M\.D\..*Farley, James A\.',
                    response.content, "control access - personal names")
        self.assertPattern('<h3>Topical Terms</h3>.*African Americans--Georgia--Eatonton\..*Education--Georgia\.|',
                    response.content, "control access - subjects")
        self.assertPattern('<h3>Geographic Names</h3>.*Augusta \(Ga\.\).*Eatonton \(Ga\.\)',
                    response.content, "control access - geography")
        self.assertPattern('<h3>Form/Genre Terms</h3>.*Photographs\..*Scrapbooks\.',
                    response.content, "control access - form/genre")
        self.assertPattern('<h3>Occupation</h3>.*Educator\..*Journalist',
                    response.content, "control access - occupation")

        # dsc
        self.assertPattern('<h2>.*Container List.*</h2>', response.content,
            "simple finding aid (leverette) view includes container list")
        self.assertPattern('Box.*Folder.*Content.*Scrapbook 1.*MF1', response.content,
            "Scrapbook 1 in container list")
        self.assertPattern('MF1.*1.*Photo and clippings re Fannie Lee Leverette',
            response.content, "photo clippings in container list")
        self.assertPattern('MF1.*4.*Family and personal photos|', response.content,
            "family photos in container list")

        # format_ead
        response = self.client.get('/documents/pomerantz890.xml')
        self.assertPattern(r'''Sweet Auburn</[-A-Za-z]+>\s*research files''', response.content) # title

        # Title appears twice, we need to check both locations, 'EAD title' and 'Descriptive Summary'
        self.assertPattern(r'''<h1[^>]*>.*\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn''', response.content) # EAD title
        self.assertPattern(r'''<table id="descriptive_summary">.*\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn''', response.content) # Descriptive Summary title

        self.assertPattern(r'''book,\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn:''', response.content) # abstract
        self.assertPattern(r'''\[after identification of item\(s\)\],\s+<[-A-Za-z="' ]+>Where Peachtree''', response.content) # admin_info
        self.assertPattern(r'''joined\s+<[-A-Za-z="' ]+>The Washington Post''', response.content) # collection description

        # only descriptive information that is present
        response = self.client.get('/documents/bailey807')
        self.assertNotContains(response, 'Creator:')

    def test_view__fa_with_series(self):
        response = self.client.get('/documents/abbey244')
        self.assertEquals(response.status_code, 200)

        # admin info fields not present in leverette
        self.assertPattern('Related Materials in This Repository.*William Butler Yeats collection',
            response.content, "admin info - related materials")
        self.assertPattern('Historical Note.*Abbey Theatre, organized in 1904',
            response.content, "admin info - historical note")
        self.assertPattern('Arrangement Note.*Organized into three series',
            response.content, "admin info - arrangement")

        # series instead of container list
        self.assertPattern('<h2>.*Description of Series.*</h2>', response.content,
            "finding aid with series includes description of series")
        self.assertPattern('<a href.*>Series 1: Plays</a>', response.content,
            "series 1 link")
        self.assertPattern('<a href.*>Series 2: Programs.*</a>', response.content,
            "series 2 link")
        self.assertPattern('|<a href.*>Series 3: Other material, 1935-1941.*</a>',
            response.content, "series 3 link")

    def test_view__fa_with_subseries(self):
        response = self.client.get('/documents/raoul548')
        self.assertEquals(response.status_code, 200)

        # admin info fields not present in previous fixtures
        self.assertPattern('Related Materials in Other Repositories.*original Wadley diaries',
            response.content, "admin info - related materials")

        # collection description - multiple paragraphs
        self.assertPattern('Biographical Note.*centered in Georgia.*eleven children.*moved to New York',
            response.content, "collection description - bio with multiple paragraphs")      # text from first 3 paragraphs
        self.assertPattern('Scope and Content Note.*contain letters, journals.*arranged in four series.*document the life',
            response.content, "collection description - scote & content with multiple paragraphs")

        # series instead of container list
        self.assertPattern('<h2>.*Description of Series.*</h2>', response.content,
            "series instead of container list")
        self.assertPattern('<a href.*>Series 1: Letters and personal papers.*</a>',
            response.content, "series 1 link")
        self.assertPattern('<a href.*>Subseries 1\.1: William Greene Raoul paper.*</a>',
            response.content, "subseries 1.1 link")
        self.assertPattern('<a href.*>Subseries 1\.2: Mary Wadley Raoul papers.*</a>',
            response.content, "subseries 1.2 link")
        self.assertPattern('<a href.*>Subseries 1\.13: .*Norman Raoul papers.*</a>',
            response.content, "subseries 1.13 link")
        self.assertPattern('<a href.*>Series 2:.*Photographs,.*circa.*1850-1960.*</a>',
            response.content, "series 2 link")
        self.assertPattern('<a href.*>Series 4:.*Miscellaneous,.*1881-1982.*</a>',
            response.content, "series 4 link")

    def test_view_indexentry(self):
        # main page should link to indexes in ead contents
        response = self.client.get('/documents/raoul548')
        self.assertContains(response, 'Index of Selected Correspondents')
        # index links should be full urls, not same-page anchors
        self.assertContains(response, 'href="/documents/raoul548/index1"')
        # second index
        self.assertContains(response, 'Second Index')
        self.assertContains(response, 'href="/documents/raoul548/index2"')

        # first index - on a separate page
        response = self.client.get('/documents/raoul548/index1')
        # ead title, table of contents
        self.assertContains(response, 'Raoul family papers')
        self.assertContains(response, 'Series 1')
        self.assertContains(response, 'Index of Selected Correspondents')
        # current index on TOC should not be a link
        self.assertContains(response, 'href="/documents/raoul548/index1"', 0)
        # first index name and ref
        self.assertContains(response, 'Alexander, Edwin Porter, 1835-1910')
        self.assertContains(response, 'Series 1 - 2:1 (2); 2:5 (1)')
        # last index name and ref
        self.assertContains(response, 'Woolford, T. Guy')
        self.assertContains(response, 'Series 1 - 32:4 (10); 32:5 (3)')

        # second index
        response = self.client.get('/documents/raoul548/index2')
        self.assertContains(response, 'Second Index')

        # TODO: test that current index is not linked in TOC
        # test links are not anchors


    def test_view_nodsc(self):
        response = self.client.get('/documents/adams465')
        self.assertEquals(response.status_code, 200)

        # record with no dsc - no container list or series
        self.assertNotContains(response, 'Container List')
        self.assertNotContains(response, 'Description of Series')

        # FIXME: test also not listed in top-level table of contents?

# view single series in a finding aid

    def test_view_series__bailey_series1(self):
        response = self.client.get('/documents/bailey807/bailey807_series1')
        self.assertEquals(response.status_code, 200)

        # single series page
        # - series title
        self.assertPattern('<h2>.*Series 1.*Correspondence,.*1855-1995.*</h2>',
            response.content, "series title displayed")
        # - ead title
        self.assertPattern('<h1[^>]*>.*<a href="/documents/bailey807">Bailey and Thurman.+families papers',
            response.content, "finding aid title displayed, links to main record page")
        # ead toc
        self.assertPattern('<a href="/documents/bailey807#descriptive_summary">Descriptive Summary</a>',
            response.content, "link to main finding aid descriptive summary")
        self.assertPattern('<a href="/documents/bailey807#administrative_information">Administrative Information</a>',
            response.content, "link to main finding aid admin info")
        self.assertPattern('<a href="/documents/bailey807#collection_description">Collection Description</a>',
            response.content, "link to main finding aid collection description")
        self.assertPattern('<a href="/documents/bailey807#control_access">Selected Search Terms</a>',
            response.content, "link to main finding aid control access")
        # series nav
        self.assertPattern('<li>[^<]*Series 1:.*Correspondence.*</li>',
            response.content, "series nav - current series not a link")
        self.assertPattern('<li>.*<a href="/documents/bailey807/bailey807_series2">.*Series 2:.*Writings by Bailey family.*</a>.*</li>',
            response.content, "series nav - link to series 2")
        self.assertPattern('<li>.*<a href="/documents/bailey807/bailey807_series9">.*Series 9:.*Audiovisual material.*</a>.*</li>',
            response.content, "series nav - link to series 9")

        # series contents
        self.assertPattern('1.*1.*I\. G\. Bailey, 1882-1901', response.content,
            "first content of series 1")
        self.assertPattern('2.*8.*Susie E\. Bailey, undated', response.content,
            "sample middle content of series 1")
        self.assertPattern('3.*13.*Miscellaneous correspondence, undated', response.content,
            "last content of series 1")


    def test_view_subseries__raoul_series1_6(self):
        response = self.client.get('/documents/raoul548/raoul548_1003223/raoul548_1001928')
        self.assertEquals(response.status_code, 200)

        # single series page
        # - series title
        self.assertPattern('<h2>.*Subseries 1\.6.*Gaston C\. Raoul papers,.*1882-1959.*</h2>',
            response.content, "subseries title displayed")
        # - ead title
        self.assertPattern('<h1[^>]*>.*<a href="/documents/raoul548">Raoul family papers,.*1865-1985',
            response.content, "finding aid title displayed, links to main record page")
            
        # series nav
        self.assertPattern('<li>.*<a href="/documents/raoul548/raoul548_1003223">.*Series 1:.*Letters and personal papers,.*1865-1982.*</a>.*</li>',
            response.content, "series nav - series 1 link")
        self.assertPattern('<li>.*<a href="/documents/raoul548/raoul548_1003649">.*Series 2:.*Photographs.*</a>.*</li>',
            response.content, "series nav - link to series 2")
        self.assertPattern('<li>.*<a href="/documents/raoul548/raoul548_s4">.*Series 4:.*Miscellaneous.*</a>.*</li>',
            response.content, "series nav - link to series 4")

        # descriptive info
        self.assertPattern('<h3>Biographical Note</h3>.*<p>.*born March 1.*</p>',
            response.content, "subseries biographical note")
        self.assertPattern('<h3>Scope and Content Note</h3>.*<p>.*letters to family.*</p>.*<p>.*earliest letters.*</p>',
            response.content, "subseries scope & content, 2 paragraphs")
        self.assertPattern('<h3>Arrangement Note</h3>.*<p>Arranged by record type.</p>',
            response.content, "subseries arrangment note")

        # subseries contents
        # TODO/FIXME: test for box/folder headings? test for section headings?
        self.assertPattern('20.*1.*1886-1887', response.content,
            "first content of subseries 1.6")
        self.assertPattern('22.*14.*Journal,.*1888', response.content,
            "sample middle content of subseries 1.6")
        self.assertPattern('22.*23.*1910-1912', response.content,
            "last content of subseries 1.6")

        # top-level ToC on series page should include index link
        self.assertContains(response, 'Index of Selected Correspondents')
        self.assertContains(response, 'href="/documents/raoul548/index1"')
        self.assertContains(response, 'Second Index')
        self.assertContains(response, 'href="/documents/raoul548/index2"')


    def test_view_subsubseries__raoul_series4_1a(self):
        # NOTE: raoul series 4 broken into sub-sub-series for testing, is not in original finding aid
        response = self.client.get('/documents/raoul548/raoul548_s4/raoul548_4.1/raoul548_4.1a')
        self.assertEquals(response.status_code, 200)
        
        # - sub-subseries title
        self.assertPattern('<h2>.*Subseries 4\.1a.*Genealogy.*(?!None).*</h2>',
            response.content, "sub-subseries title displayed, no physdesc")
        # - ead title
        self.assertPattern('<h1[^>]*>.*<a href="/documents/raoul548">Raoul family papers,.*1865-1985',
            response.content, "finding aid title displayed, links to main record page")

        # series nav
        self.assertPattern('<li>.*<a href="/documents/raoul548/raoul548_1003223">.*Series 1:.*Letters and personal papers,.*1865-1982.*</a>.*</li>',
            response.content, "series nav - series 1 link")
        self.assertPattern('<li>.*<a href="/documents/raoul548/raoul548_1003649">.*Series 2:.*Photographs.*</a>.*</li>',
            response.content, "series nav - link to series 2")
        self.assertPattern('<li>.*<a href="/documents/raoul548/raoul548_s4">.*Series 4:.*Miscellaneous.*</a>.*</li>',
            response.content, "series nav - link to series 4")

        # subseries contents
        self.assertPattern('46.*1.*Raoul family journal', response.content,
            "first content of sub-subseries 4.1a")
        self.assertPattern('46.*2.*Gaston Cesar Raoul', response.content,
            "last content of sub-subseries 4.1a")


        # series with <head>less scopecontent
        response = self.client.get('/documents/raoul548/raoul548_s4/rushdie1000_subseries2.1')
        self.assertContains(response, "Subseries 2.1")
        self.assertContains(response, "Additional drafts and notes")
        # missing section head should not be displayed as "none"
        self.assertContains(response, "None", 0)


# **** tests for helper functions for creating series url, list of series/subseries for display in templates

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

    def test__subseries_links_anchors(self):
        # subseries links  - generate same-page anchors instead of full urls
        fa = FindingAid.objects.get(eadid='raoul548')
        links = _subseries_links(fa.dsc, url_ids=[fa.eadid], url_callback=_series_anchor)

        self.assert_("Series 1: Letters and personal papers" in links[0])
        self.assert_("href='#raoul548_1003223'" in links[0])
        # subseries
        self.assert_("href='#raoul548_100355'" in links[1][0])



    def test_printable_fa(self):
        # using 'full' html version of pdf for easier testing
        response = self.client.get('/documents/raoul548/full')
        self.assertEquals(response.status_code, 200)        
        # publication info         
        self.assertPattern('Emory University.*Manuscript, Archives, and Rare Book Library.*Atlanta, GA 30322', response.content,
            "publication statement included")

        # NOTE: using same section templates as other views, which are tested more thoroughly above
        # here, just checking that appropriate sections are present

        # description
        self.assertContains(response, "Descriptive Summary")
        # controlaccess not included in print copy
        self.assertContains(response, "Selected Search Terms", 0)
        # series list, and all series down to c03 level
        self.assertContains(response, "Description of Series")
        # series links are anchors in the same page
        self.assertPattern('<a href=\'#raoul548_s1\.10\'>Subseries 1.10', response.content)
        self.assertPattern('<h2 class="series">.*Series 1 .*Letters and personal papers,.* 1865-1982.*</h2>', response.content)
        self.assertPattern('<h2 class="subseries">.*Subseries 1.2 .*Mary Wadley Raoul papers,.* 1865-1936.*</h2>', response.content)
        # index
        self.assertContains(response, "Index of Selected Correspondents")
        # second index
        self.assertContains(response, "Second Index")

        # simple finding aid with no subseries - should have container list
        response = self.client.get('/documents/leverette135/full')
        self.assertContains(response, "Container List")

    def test_ead_lastmodified(self):
        modified = _ead_lastmodified('rqst', 'abbey244')
        self.assert_(isinstance(modified, datetime),
                     "_ead_lastmodified should return a datetime object")
        today = datetime.now()
        date_format = '%Y-%m-%d'
        expected = datetime.now().strftime(date_format)
        value = modified.strftime(date_format)
        self.assertEqual(expected, value,
                     'ead lastmodified should be today, expected %s, got %s' % (expected, value))

        # invalid eadid
        self.assertRaises(Http404, _ead_lastmodified, 'rqst', 'bogusid')
        

    def test_ead_etag(self):
        checksum = _ead_etag('rqst', 'abbey244')
        self.assert_(re.match('[0-9a-f]{40}$', checksum),
                     'ead etag should be 40-character hex checksum, got %s' % checksum)
        # invalid eadid
        self.assertRaises(Http404, _ead_lastmodified, 'rqst', 'bogusid')


class FullTextFaViewsTest(TestCase):
    # test for views that require eXist full-text index
    exist_fixtures = { 'index' : exist_index_path,
                       'directory' : exist_fixture_path }

    def test_keyword_search(self):
        response = self.client.get('/search/', { 'keywords' : 'raoul'})
        self.assertEquals(response.status_code, 200)

        self.assertPattern("<p[^>]*>Search results for : .*raoul.*</p>", response.content)
        self.assertContains(response, "1 finding aid found")
        self.assertContains(response, "/documents/raoul548")
        self.assertContains(response, "<div class=\"relevance\">")

        response = self.client.get('/search/', { 'keywords' : 'family papers'})
        self.assertEquals(response.status_code, 200)
        self.assertPattern("<p[^>]*>Search results for : .*family papers.*</p>", response.content)
        self.assertContains(response, "5 finding aids found")
        self.assertContains(response, "Fannie Lee Leverette scrapbooks")
        self.assertContains(response, "Raoul family papers")
        self.assertContains(response, "Bailey and Thurman families papers")
        self.assertContains(response, "Abbey Theatre collection")
        self.assertContains(response, "Pomerantz, Gary M.")
        self.assertContains(response, "<div class=\"relevance\">", 5)

        response = self.client.get('/search/', { 'keywords' : 'nonexistentshouldmatchnothing'})
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "No finding aids matched")
