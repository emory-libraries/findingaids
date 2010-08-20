from datetime import datetime
from os import path
import re
from time import sleep
from types import ListType
from lxml import etree

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404, HttpRequest
from django.template import RequestContext, Template
from django.test import Client, TestCase as DjangoTestCase

from eulcore.xmlmap  import load_xmlobject_from_file, load_xmlobject_from_string, XmlObject
from eulcore.django.existdb.db import ExistDB
from eulcore.django.test import TestCase

from findingaids.fa.models import FindingAid, Series, Subseries, Subsubseries, Deleted
from findingaids.fa.views import _series_url, _subseries_links, _series_anchor
from findingaids.fa.templatetags.ead import format_ead
from findingaids.fa.utils import pages_to_show, ead_lastmodified, ead_etag, \
    collection_lastmodified, exist_datetime_with_timezone

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

        #dc_subjects
        self.assert_(u'Irish drama--20th century.' in self.findingaid['abbey244'].dc_subjects)
        self.assert_(u'Theater--Ireland--20th century.' in self.findingaid['abbey244'].dc_subjects)
        self.assert_(u'Dublin (Ireland)' in self.findingaid['abbey244'].dc_subjects)
        #dc_contributors
        self.assert_(u'Bailey, I. G. (Issac George), 1847-1914.' in self.findingaid['bailey807'].dc_contributors)
        self.assert_(u'Bailey, Susie E., d. 1948.' in self.findingaid['bailey807'].dc_contributors)
        self.assert_(u'Thurman, Howard, 1900-1981.' in self.findingaid['bailey807'].dc_contributors)
        self.assert_(u'Thurman, Sue Bailey.' in self.findingaid['bailey807'].dc_contributors)

    def test_series_info(self):
        info = self.findingaid['raoul548'].dsc.c[0].series_info()
        self.assert_(isinstance(info, ListType))
        self.assertEqual("Scope and Content Note", unicode(info[0].head))
        self.assertEqual("Arrangement Note", unicode(info[1].head))

        #get number of matched keywords in series
        self.assertEqual(self.findingaid['raoul548'].dsc.c[3].match_count,  2)

        #get number of matched keywords in index
        self.assertEqual(self.findingaid['raoul548'].archdesc.index[0].match_count,  1)
        
        # series info problem when scopecontent is missing a <head>; contains use restriction
        info = self.findingaid['raoul548'].dsc.c[-1].c[-1].series_info()
        self.assert_(isinstance(info, ListType))
        self.assert_("contains all materials related to " in info[0].content[0].__unicode__()) # scopecontent with no head
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
        # TODO: dc:identifier will be ARK, once we add them
        #self.assert_("abbey244" in fields["identifier"])

        fields = self.findingaid['bailey807'].dc_fields()
        self.assert_("Bailey, I. G. (Issac George), 1847-1914." in fields["contributor"])
        self.assert_("Bailey, Susie E., d. 1948." in fields["contributor"])
        self.assert_("Thurman, Howard, 1900-1981." in fields["contributor"])
        self.assert_("Thurman, Sue Bailey." in fields["contributor"])


class FaViewsTest(TestCase):
    exist_fixtures = {'directory' : exist_fixture_path }
    # NOTE: views that require full-text search tested separately below for response-time reasons

    def setUp(self):
        self.client = Client()
        self.db = ExistDB()

    def tearDown(self):
        pass
     
    def test_title_letter_list(self):
        titles_url = reverse('fa:browse-titles')
        response = self.client.get(titles_url)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s'
                             % (expected, response.status_code, titles_url))

        # first letters from 4 test documents
        for letter in ['A', 'B', 'L', 'R']:        
            self.assertContains(response, 'href="%s"' % \
                reverse('fa:titles-by-letter', kwargs={'letter':letter}),
                msg_prefix="browse titles should link to titles starting with %s    " % letter)

        # should not include first letters not present in the data
        self.assertContains(response, 'href="%s"' % \
                reverse('fa:titles-by-letter', kwargs={'letter':'Z'}), 0,
                msg_prefix='browse titles should not link to titles starting with Z')

    def test_titles_by_letter(self):
        a_titles = reverse('fa:titles-by-letter', kwargs={'letter':'A'})
        response = self.client.get(a_titles)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s'
                             % (expected, response.status_code, a_titles))
        self.assertContains(response, 'href="%s' % \
            reverse('fa:view-fa', kwargs={'id': 'abbey244'}),
            msg_prefix='browse by titles for A should link to Abbey finding aid')
        self.assertContains(response, '<p class="abstract">Collection of play scripts',
            msg_prefix='browse by titles for A should include Abbey finding aid abstract')
        self.assertContains(response, '2 finding aids found',
            msg_prefix='browse by titles for A should return 2 finding aids')
        # test pagination ?

        # test current letter
        self.assertPattern("<a *class='current'[^>]*>A<", response.content,
            msg_prefix='browse by letter A should mark A as current letter')

        # format_ead
        response = self.client.get(reverse('fa:titles-by-letter', kwargs={'letter':'P'}))
        # title
        self.assertPattern(r'''Sweet Auburn</[-A-Za-z]+> research files''',
            response.content, msg_prefix='title with formatting should be formatted in list view')
        # abstract
        self.assertPattern(r'''book,\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn:''',
            response.content, msg_prefix='abstract with formatting should be formatted in list view') 

        # no finding aids
        response = self.client.get(reverse('fa:titles-by-letter', kwargs={'letter':'Z'}))
        self.assertPattern('<div>No finding aids found for .*Z.*</div>', response.content,
            msg_prefix="titles by letter 'Z' should return no finding aids")

        response = self.client.get(reverse('fa:titles-by-letter', kwargs={'letter':'B'}))

        # finding aid with no origination - unit title used as browse title & link   
        # - unit title should only be displayed once
        self.assertContains(response, 'Bailey and Thurman families papers', 1,
            msg_prefix="finding aid with no origination should use unit title once as title & link")
        
        # Additional case for doubled title problem -title with formatting
        response = self.client.get(reverse('fa:titles-by-letter', kwargs={'letter':'P'}))
        self.assertContains(response, 'Pitts v. Freeman', 2) # Title and abstract
        #title within unittitle
        self.assertPattern(r'''Pitts v. Freeman</[-A-Za-z]+> school''', response.content,
            msg_prefix='title within unittitle should be formatted on list view')
    

# view finding aid main page

    def test_view_notfound(self):
        nonexistent_ead = reverse('fa:view-fa', kwargs={'id': 'nonexistent'})
        response = self.client.get(nonexistent_ead)
        expected = 404
        self.assertEqual(response.status_code, expected, 
                        'Expected %s but returned %s for nonexistent EAD at %s'
                            % (expected, response.status_code, nonexistent_ead))

    def test_deleted(self):
        # 410 gone - not found in exist, but there is a record indicating it was deleted
        # create a Deleted record for testing
        id, title, note = 'deleted', 'Deleted EAD record', 'removed because of foo'
        Deleted(eadid=id, title=title, note=note).save()

        # test a deleted record in all 3 single-finding aid top-level views
        # view_fa (main html view)
        fa_url = reverse('fa:view-fa', kwargs={'id': id})
        response = self.client.get(fa_url)
        expected, got = 410, response.status_code
        self.assertEqual(expected, got,
                'Expected %s but returned %s for deleted EAD at %s' % \
                 (expected, response.status_code, fa_url))
        self.assertContains(response, '<h1>%s</h1>' % title, status_code=410,
                msg_prefix="title from deleted record is displayed in response")
        self.assertContains(response, note, status_code=410,
                msg_prefix="note from deleted record are displayed in response")
        
        # full_fa (single-page html version of entire Finding Aid, basis for PDF)
        full_url = reverse('fa:full-fa', kwargs={'id': id})
        response = self.client.get(full_url)
        expected, got = 410, response.status_code
        self.assertEqual(expected, got, 
                'Expected %s but returned %s for deleted EAD at %s' % \
                 (expected, response.status_code, full_url))
        self.assertContains(response, '<h1>%s</h1>' % title, status_code=410,
                msg_prefix="title from deleted record is displayed in response")

        # printable_fa - single-page PDF of entire Finding Aid
        pdf_url = reverse('fa:printable-fa', kwargs={'id': id})
        response = self.client.get(pdf_url)
        expected, got = 410, response.status_code
        self.assertEqual(expected, got,
                'Expected %s but returned %s for deleted EAD at %s' % \
                 (expected, response.status_code, pdf_url))
        self.assertContains(response, '<h1>%s</h1>' % title, status_code=410,
                msg_prefix="title from deleted record is displayed in response")

        # xml_fa - full XML EAD content for a single finding aid
        xml_url = reverse('fa:xml-fa', kwargs={'id': id})
        response = self.client.get(xml_url)
        expected, got = 410, response.status_code
        self.assertEqual(expected, got,
                'Expected %s but returned %s for deleted EAD at %s' % \
                 (expected, response.status_code, full_url))
        self.assertContains(response, '<h1>%s</h1>' % title, status_code=410,
                msg_prefix="title from deleted record is displayed in response")


    def test_view_dc_fields(self):
        response = self.client.get(reverse('fa:view-fa', kwargs={'id': 'abbey244'}))
        # TODO: would be nice to validate the DC output...  (if possible)
        
        #DC.creator
        self.assertContains(response, '<meta name="DC.creator" content="Abbey Theatre." />')
        #DC.publisher
        self.assertContains(response, '<meta name="DC.publisher" content="Emory University" />')
        #date
        self.assertContains(response, '<meta name="DC.date" content="2002-02-24" />')
        #language
        self.assertContains(response, '<meta name="DC.language" content="eng" />')
        #dc_subjects
        self.assertContains(response, '<meta name="DC.subject" content="Irish drama--20th century." />')
        self.assertContains(response, '<meta name="DC.subject" content="Theater--Ireland--20th century." />')
        self.assertContains(response, '<meta name="DC.subject" content="Dublin (Ireland)" />')
        #identifier - TODO (use ARK)
        #self.assertContains(response, '<meta name="DC.identifier" content="abbey244" />')

        response = self.client.get(reverse('fa:view-fa', kwargs = {'id': 'bailey807'}))
        #title
        self.assertContains(response, '<meta name="DC.title" content="Bailey and Thurman families papers, circa 1882-1995" />')
        #dc_contributors
        self.assertContains(response, '<meta name="DC.contributor" content="Bailey, I. G. (Issac George), 1847-1914." />')
        self.assertContains(response, '<meta name="DC.contributor" content="Bailey, Susie E., d. 1948." />')
        self.assertContains(response, '<meta name="DC.contributor" content="Thurman, Howard, 1900-1981." />')
        self.assertContains(response, '<meta name="DC.contributor" content="Thurman, Sue Bailey." />')
       
    def test_view_simple(self):
        fa_url = reverse('fa:view-fa', kwargs={'id': 'leverette135'})
        response = self.client.get(fa_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, fa_url))

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

        # title with formatting
        response = self.client.get(reverse('fa:view-fa', kwargs={'id': 'pomerantz890.xml'}))
        self.assertPattern(r'''Sweet Auburn</[-A-Za-z]+>\s*research files''', response.content) # title
        # Title appears twice, we need to check both locations, 'EAD title' and 'Descriptive Summary'
        self.assertPattern(r'''<h1[^>]*>.*\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn''', response.content) # EAD title
        self.assertPattern(r'''<table id="descriptive_summary">.*\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn''', response.content) # Descriptive Summary title

        self.assertPattern(r'''book,\s+<[-A-Za-z="' ]+>Where Peachtree Meets Sweet Auburn:''', response.content) # abstract
        self.assertPattern(r'''\[after identification of item\(s\)\],\s+<[-A-Za-z="' ]+>Where Peachtree''', response.content) # admin_info
        self.assertPattern(r'''joined\s+<[-A-Za-z="' ]+>The Washington Post''', response.content) # collection description

        # only descriptive information that is present
        response = self.client.get(reverse('fa:view-fa', kwargs={'id': 'bailey807'}))
        self.assertNotContains(response, 'Creator:')

        # header link to EAD xml
        response = self.client.get(reverse('fa:view-fa', kwargs={'id': 'pomerantz890.xml'}))
        self.assertContains(response, 'href="%s"' % reverse('fa:xml-fa', kwargs={'id': 'pomerantz890.xml'}))

        self.assertNotContains(response, '<meta name="robots" content="noindex,nofollow"',
            msg_prefix="non-highlighted finding aid does NOT include robots directives noindex, nofollow")

    def test_view__fa_with_series(self):
        fa_url = reverse('fa:view-fa', kwargs={'id': 'abbey244'})
        response = self.client.get(fa_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, fa_url))

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
        fa_url = reverse('fa:view-fa', kwargs={'id': 'raoul548'})
        response = self.client.get(fa_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, fa_url))

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
        response = self.client.get(reverse('fa:view-fa', kwargs={'id': 'raoul548'}))
        self.assertContains(response, 'Index of Selected Correspondents',
            msg_prefix='main finding aid page should list Index title')
        # index links should be full urls, not same-page anchors
        index_url = reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'index1'})
        self.assertContains(response, 'href="%s"' % index_url,
            msg_prefix='main finding aid page should link to index page')
        # second index
        self.assertContains(response, 'Second Index',
            msg_prefix='main finding aid page should list second Index title')
        index2_url = reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'index2'})
        self.assertContains(response, 'href="%s"' % index2_url,
            msg_prefix='main finding aid page should link to second index page')

        # first index - on a separate page
        
        response = self.client.get(index_url)
        # ead title, table of contents
        self.assertContains(response, 'Raoul family papers',
            msg_prefix="finding aid index page includes main finding aid title")
        self.assertContains(response, 'Series 1',
            msg_prefix='finding aid index page includes series listing')
        self.assertContains(response, 'Index of Selected Correspondents',
            msg_prefix='finding aid index page includes current index title')
        # current index on TOC should not be a link
        self.assertContains(response, 'href="%s"' % index_url, 0,
            msg_prefix='current index is not a link in finding aid ToC')
        # should link to other index
        self.assertContains(response, 'href="%s"' % index2_url,
            msg_prefix='index page includes link to second index in finding aid ToC')
        # first index name and ref
        self.assertContains(response, 'Alexander, Edwin Porter, 1835-1910',
            msg_prefix='first index name is listed on index page')
        self.assertContains(response, 'Series 1 - 2:1 (2); 2:5 (1)',
            msg_prefix='first index reference is listed on index page')
        # last index name and ref
        self.assertContains(response, 'Woolford, T. Guy',
            msg_prefix='last index name is listed on index page')
        self.assertContains(response, 'Series 1 - 32:4 (10); 32:5 (3)',
            msg_prefix='reference from last index name is listed on index page')

        # second index also retrieves
        response = self.client.get(index2_url)
        self.assertContains(response, 'Second Index')


    def test_view_nodsc(self):
        fa_url = reverse('fa:view-fa', kwargs={'id': 'adams465'})
        response = self.client.get(fa_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, fa_url))

        # record with no dsc - no container list or series
        self.assertNotContains(response, 'Container List',
            msg_prefix='finding aid with no dsc does not include a container list')
        self.assertNotContains(response, 'Description of Series',
            msg_prefix='finding aid with no dsc does not include a description of series')

        # FIXME: test also not listed in top-level table of contents?

    # view single series in a finding aid
    def test_view_series__bailey_series1(self):
        series_url = reverse('fa:series-or-index', kwargs={'id': 'bailey807',
            'series_id': 'bailey807_series1'})
        response = self.client.get(series_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, series_url))

        fa_url = reverse('fa:view-fa', kwargs={'id': 'bailey807'})
        # single series page
        # - series title
        self.assertPattern('<h2>.*Series 1.*Correspondence,.*1855-1995.*</h2>',
            response.content, "series title displayed")
        # - ead title
        self.assertPattern('<h1[^>]*>.*<a href="%s" rel=\"contents\">Bailey and Thurman.+families papers' % fa_url,
            response.content, "finding aid title displayed, links to main record page")
        # ead toc
        self.assertPattern('<a href="%s#descriptive_summary">Descriptive Summary</a>' % fa_url,
            response.content, "link to main finding aid descriptive summary")
        self.assertPattern('<a href="%s#administrative_information">Administrative Information</a>' % fa_url,
            response.content, "link to main finding aid admin info")
        self.assertPattern('<a href="%s#collection_description">Collection Description</a>' % fa_url,
            response.content, "link to main finding aid collection description")
        self.assertPattern('<a href="%s#control_access">Selected Search Terms</a>' % fa_url,
            response.content, "link to main finding aid control access")
        # series nav
        self.assertPattern('<li>[^<]*Series 1:.*Correspondence.*</li>',
            response.content, "series nav - current series not a link")
        self.assertPattern('<li>.*<a href="%s".*rel="next">.*Series 2:.*Writings by Bailey family.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'bailey807', 'series_id': 'bailey807_series2'}),
            response.content, "series nav - link to series 2")
        self.assertPattern('<li>.*<a href="%s".*>.*Series 9:.*Audiovisual material.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'bailey807', 'series_id': 'bailey807_series9'}),
            response.content, "series nav - link to series 9")

        # series contents
        self.assertPattern('1.*1.*I\. G\. Bailey, 1882-1901', response.content,
            "first content of series 1")
        self.assertPattern('2.*8.*Susie E\. Bailey, undated', response.content,
            "sample middle content of series 1")
        self.assertPattern('3.*13.*Miscellaneous correspondence, undated', response.content,
            "last content of series 1")

        self.assertNotContains(response, '<meta name="robots" content="noindex,nofollow"',
            msg_prefix="non-highlighted series does NOT include robots directives noindex, nofollow")

    def test_view_subseries__raoul_series1_6(self):
        subseries_url = reverse('fa:view-subseries', kwargs={'id': 'raoul548',
            'series_id': 'raoul548_1003223', 'subseries_id': 'raoul548_1001928'})
        response = self.client.get(subseries_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, subseries_url))

        # single series page
        # - series title
        self.assertPattern('<h2>.*Subseries 1\.6.*Gaston C\. Raoul papers,.*1882-1959.*</h2>',
            response.content, "subseries title displayed")
        # - ead title
        self.assertPattern('<h1[^>]*>.*<a href="%s" rel="contents">Raoul family papers,.*1865-1985' % \
            reverse('fa:view-fa', kwargs={'id': 'raoul548'}),
            response.content, "finding aid title displayed, links to main record page")
            
        # series nav
        self.assertPattern('<li>.*<a href="%s".*rel="start">.*Series 1:.*Letters and personal papers,.*1865-1982.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223'}),
            response.content, "series nav - series 1 link")
        self.assertPattern('<li>.*<a href="%s".*rel="next">.*Series 2:.*Photographs.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003649'}),
            response.content, "series nav - link to series 2")
        self.assertPattern('<li>.*<a href="%s".*>.*Series 4:.*Miscellaneous.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4'}),
            response.content, "series nav - link to series 4")

        # descriptive info
        self.assertPattern('<h3>Biographical Note</h3>.*<p>.*born March 1.*</p>',
            response.content, "subseries biographical note")
        self.assertPattern('<h3>Scope and Content Note</h3>.*<p>.*letters to family.*</p>.*<p>.*earliest letters.*</p>',
            response.content, "subseries scope & content, 2 paragraphs")
        self.assertPattern('<h3>Arrangement Note</h3>.*<p>Arranged by record type.</p>',
            response.content, "subseries arrangment note")

        # subseries contents
        self.assertPattern('20.*1.*1886-1887', response.content,
            "first content of subseries 1.6")
        self.assertPattern('22.*14.*Journal,.*1888', response.content,
            "sample middle content of subseries 1.6")
        self.assertPattern('22.*23.*1910-1912', response.content,
            "last content of subseries 1.6")

        # top-level ToC on series page should include index link
        self.assertContains(response, 'Index of Selected Correspondents',
            msg_prefix="subseries ToC lists index title")
        self.assertContains(response, 'href="%s"' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'index1'}),
            msg_prefix="subseries ToC links to index")
        self.assertContains(response, 'Second Index',
            msg_prefix='subseries ToC lists second index title')
        self.assertContains(response, 'href="%s"' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'index2'}),
            msg_prefix='subseries ToC links to second index')


    def test_view_subsubseries__raoul_series4_1a(self):
        # NOTE: raoul series 4 broken into sub-sub-series for testing, is not in original finding aid
        subsubseries_url = reverse('fa:view-subsubseries', kwargs={'id': 'raoul548',
            'series_id': 'raoul548_s4', 'subseries_id': 'raoul548_4.1',
            'subsubseries_id': 'raoul548_4.1a'})
        response = self.client.get(subsubseries_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, subsubseries_url))
        
        # - sub-subseries title
        self.assertPattern('<h2>.*Subseries 4\.1a.*Genealogy.*(?!None).*</h2>',
            response.content, "sub-subseries title displayed, no physdesc")
        # - ead title
        self.assertPattern('<h1[^>]*>.*<a href="%s" rel="contents">Raoul family papers,.*1865-1985' % \
            reverse('fa:view-fa', kwargs={'id': 'raoul548'}),
            response.content, "finding aid title displayed, links to main record page")

        # series nav
        self.assertPattern('<li>.*<a href="%s".*rel="start">.*Series 1:.*Letters and personal papers,.*1865-1982.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223'}),
            response.content, "series nav - series 1 link")
        self.assertPattern('<li>.*<a href="%s.* rel="next">.*Series 2:.*Photographs.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003649'}),
            response.content, "series nav - link to series 2")
        self.assertPattern('<li>.*<a href="%s".*>.*Series 4:.*Miscellaneous.*</a>.*</li>' % \
            reverse('fa:series-or-index', kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4'}),
            response.content, "series nav - link to series 4")

        # subseries contents
        self.assertPattern('46.*1.*Raoul family journal', response.content,
            "first content of sub-subseries 4.1a")
        self.assertPattern('46.*2.*Gaston Cesar Raoul', response.content,
            "last content of sub-subseries 4.1a")


        # series with <head>less scopecontent
        subseries_url = reverse('fa:view-subseries', kwargs={'id': 'raoul548',
            'series_id': 'raoul548_s4', 'subseries_id': 'rushdie1000_subseries2.1'})
        response = self.client.get(subseries_url)
        #print response
        self.assertContains(response, "Subseries 2.1")
        self.assertContains(response, "Additional drafts and notes")
        # missing section head should not be displayed as "none"
        self.assertContains(response, "None", 0,
            msg_prefix="series with a section with no head does not display 'None' for heading")


    def test_preview_mode(self):
        # test preview mode of all main finding aid views

        # load fixture to preview collection
        fullpath = path.join(settings.BASE_DIR, 'fa', 'fixtures', 'raoul548.xml')
        self.db.load(open(fullpath, 'r'), settings.EXISTDB_PREVIEW_COLLECTION + '/raoul548.xml',
                overwrite=True)
        fa_url = reverse('fa-admin:preview:view-fa', kwargs={'id': 'raoul548'})
        response = self.client.get(fa_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, fa_url))

        ead_url = reverse('fa-admin:preview:xml-fa', kwargs={'id':'raoul548'})
        self.assertContains(response, 'href="%s"' % ead_url)


        series_url = reverse('fa-admin:preview:series-or-index',
                        kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223'})
        self.assertContains(response, 'href="%s"' % series_url,
            msg_prefix='preview version of main finding aid should link to series in preview mode')

        subseries_url = reverse('fa-admin:preview:view-subseries',
                        kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
                                'subseries_id': 'raoul548_100355'})
        self.assertContains(response, "href='%s'" % subseries_url,
            msg_prefix='preview version of main finding aid should link to subseries in preview mode')

        index_url = reverse('fa-admin:preview:series-or-index',
                        kwargs={'id': 'raoul548', 'series_id': 'index1'})
        self.assertContains(response, 'href="%s"' % index_url,
            msg_prefix='preview version of main finding aid should link to index in preview mode')
        # publish form - requires logging in, really an admin feature - tested in fa_admin.tests

        # load series page
        series_url = reverse('fa-admin:preview:series-or-index',
                              kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223'})
        response = self.client.get(series_url)
        self.assertContains(response, 'href="%s"' % fa_url,
            msg_prefix='preview version of series should link to main finding aid page in preview mode')
        self.assertContains(response, 'href="%s"' % index_url,
            msg_prefix='preview version of series should link to index in preview mode')

        # clean up
        self.db.removeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/raoul548.xml')

        # non-preview page should *NOT* include publish form
        response = self.client.get(reverse('fa:view-fa', kwargs={'id': 'raoul548'}))
        self.assertNotContains(response, '<form id="preview-publish" ',
                msg_prefix="non-preview finding aid page should not include publish form")

# **** tests for helper functions for creating series url, list of series/subseries for display in templates

    def test__series_url(self):
        self.assertEqual(reverse('fa:series-or-index', kwargs={'id': 'docid', 'series_id': 's1'}),
             _series_url('docid', 's1'))
        self.assertEqual(reverse('fa:view-subseries',
            kwargs={'id': 'docid', 'series_id': 's1', 'subseries_id': 's1.2'}),
            _series_url('docid', 's1', 's1.2'))
        self.assertEqual(reverse('fa:view-subsubseries',
            kwargs={'id': 'docid', 'series_id': 's3', 'subseries_id': 's3.5', 'subsubseries_id': 's3.5a'}),
            _series_url('docid', 's3', 's3.5', 's3.5a'))

    def test__subseries_links__dsc(self):
        # subseries links for a top-level series that has subseries
        fa = FindingAid.objects.get(eadid='raoul548')
        links = _subseries_links(fa.dsc, url_ids=[fa.eadid])
        
        self.assert_("Series 1: Letters and personal papers" in links[0])
        self.assert_("href='%s'" %  reverse('fa:series-or-index',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223'})
            in links[0])
        # nested list for subseries
        self.assert_(isinstance(links[1], ListType))
        self.assert_("Subseries 1.1: William Greene" in links[1][0])
        self.assert_("href='%s'" % reverse('fa:view-subseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
            'subseries_id': 'raoul548_100355'})    in links[1][0])

        # second-to-last entry - series 4
        self.assert_("Series 4: Misc" in links[-2])
        self.assert_("href='%s'" % reverse('fa:series-or-index',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4'}) in links[-2])
        # last entry - series 4 subseries
        self.assert_(isinstance(links[-1], ListType))
        self.assert_("Subseries 4.1:" in links[-1][0])
        # series 4.1 sub-subseries
        self.assert_(isinstance(links[-1][1], ListType))
        self.assert_("Subseries 4.1a:" in links[-1][1][0])

        # url params to add to url (e.g., keyword search terms)
        links = _subseries_links(fa.dsc, url_ids=[fa.eadid], url_params='?keywords=search+me')
        self.assert_("?keywords=search+me'" in links[0]) # series url
        self.assert_("?keywords=search+me'" in links[1][0]) # subseries url


    def test__subseries_links(self):
        # subseries links for a top-level series that has subseries
        series = Series.objects.also('ead__eadid').get(id='raoul548_1003223')
        links = _subseries_links(series)
        
        self.assertEqual(13, len(links))  # raoul series has subseries 1-13
        self.assert_("href='%s'" % reverse('fa:view-subseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
            'subseries_id': 'raoul548_100904'}) in links[2])
        self.assert_('Subseries 1.1: William Greene' in links[0])
        self.assert_("href='%s'" % reverse('fa:view-subseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
            'subseries_id': 'raoul548_100355'}) in links[0])
        self.assert_('Subseries 1.2: Mary Wadley' in links[1])
        self.assert_("href='%s'" % reverse('fa:view-subseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
            'subseries_id': 'raoul548_100529'}) in links[1])
        self.assert_('Subseries 1.3: Sarah Lois' in links[2])
        self.assert_("href='%s'" % reverse('fa:view-subseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
            'subseries_id': 'raoul548_100904'}) in links[2])
        self.assert_('Subseries 1.13: Norman Raoul' in links[-1])
        self.assert_("href='%s'" % reverse('fa:view-subseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
            'subseries_id': 'raoul548_1003222'}) in links[-1])


         # check to make suare highlighting   info is correct
        series = Series.objects.also('ead__eadid').get(id='raoul548_s4')
        links = _subseries_links(series)
        self.assertPattern("^((?!class='exist-match').)*$", links[0])       # NO matches for this link
        self.assertPattern(".*class='exist-match'.*1 match", links[2])       # matched 1 time on this link

        series = Series.objects.get(id='raoul548_1003223')
        # should get exception when top-level ead id is not available
        self.assertRaises(Exception, _subseries_links, series)


    def test__subseries_links_nested(self):
        # subseries links for a top-level series that has subseries with sub-subseries (nested list)
        series = Series.objects.also('ead__eadid').get(id='raoul548_s4')
        links = _subseries_links(series)

        self.assert_("Subseries 4.1: Misc" in links[0])
        self.assert_("href='%s'" % reverse('fa:view-subseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4',
            'subseries_id': 'raoul548_4.1'}) in links[0])
        self.assert_(isinstance(links[1], ListType))
        self.assert_("Subseries 4.1a: Genealogy" in links[1][0])
        self.assert_("href='%s'" % reverse('fa:view-subsubseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4',
            'subseries_id': 'raoul548_4.1', 'subsubseries_id': 'raoul548_4.1a'}) in links[1][0])
        self.assert_("Subseries 4.1b: Genealogy part 2" in links[1][1])
        self.assert_("href='%s'" % reverse('fa:view-subsubseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4',
            'subseries_id': 'raoul548_4.1', 'subsubseries_id': 'raoul548_4.1b'}) in links[1][1])
        

    def test__subseries_links_c02(self):
        # subseries links when not starting at c01 level
        series = Subseries.objects.also('ead__eadid', 'series__id').get(id='raoul548_4.1')
        links = _subseries_links(series)

        self.assertEqual(2, len(links))     # test doc has two c03 subseries
        self.assert_("Subseries 4.1a: Genealogy" in links[0])
        self.assert_("href='%s'" % reverse('fa:view-subsubseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4',
            'subseries_id': 'raoul548_4.1', 'subsubseries_id': 'raoul548_4.1a'}) in links[0])
        self.assert_("Subseries 4.1b: Genealogy part 2" in links[1])
        self.assert_("href='%s'" % reverse('fa:view-subsubseries',
            kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4',
            'subseries_id': 'raoul548_4.1', 'subsubseries_id': 'raoul548_4.1b'}) in links[1])

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
        self.assert_("rel='section'" in links[0])
        # subseries
        self.assert_("href='#raoul548_100355'" in links[1][0])
        self.assert_("rel='subsection'" in links[1][0])



    def test_printable_fa(self):
        # using 'full' html version of pdf for easier testing
        fullfa_url = reverse('fa:full-fa', kwargs={'id': 'raoul548'})
        response = self.client.get(fullfa_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, fullfa_url))
        # publication infor
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
        self.assertPattern('<a href=\'#raoul548_s1\.10\' rel=\'subsection\'>Subseries 1.10', response.content)
        self.assertPattern('<h2 class="series">.*Series 1 .*Letters and personal papers,.* 1865-1982.*</h2>', response.content)
        self.assertPattern('<h2 class="subseries">.*Subseries 1.2 .*Mary Wadley Raoul papers,.* 1865-1936.*</h2>', response.content)
        # index
        self.assertContains(response, "Index of Selected Correspondents")
        # second index
        self.assertContains(response, "Second Index")

        # simple finding aid with no subseries - should have container list
        response = self.client.get(reverse('fa:full-fa', kwargs={'id': 'leverette135'}))
        self.assertContains(response, "Container List",
            msg_prefix="finding aid with no subseries should include container list in printable mode")

        # minimal testing on actual PDF
        pdf_url = reverse('fa:printable-fa', kwargs={'id': 'raoul548'})
        response = self.client.get(pdf_url)
        expected = 'application/pdf'
        self.assertEqual(response['Content-Type'], expected,
                        "Expected '%s' but returned '%s' for %s mimetype" % \
                        (expected, response['Content-Type'], pdf_url))
        expected = 'attachment; filename=raoul548.pdf'
        self.assertEqual(response['Content-Disposition'], expected,
                        "Expected '%s' but returned '%s' for %s content-disposition" % \
                        (expected, response['Content-Disposition'], pdf_url))

    def test_xml_fa(self):
        nonexistent_ead = reverse('fa:xml-fa', kwargs={'id': 'nonexistent'})
        response = self.client.get(nonexistent_ead)
        expected = 404
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for nonexistent EAD at %s'
                            % (expected, response.status_code, nonexistent_ead))
        xml_url = reverse('fa:xml-fa', kwargs={'id': 'abbey244'})
        response = self.client.get(xml_url)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, xml_url))
        expected = 'application/xml'
        self.assertEqual(response['Content-Type'], expected,
                        "Expected '%s' but returned '%s' for %s mimetype" % \
                        (expected, response['Content-Type'], xml_url))
        self.assertContains(response, 'identifier="abbey244.xml')

        # load httpresponse body into an XmlObject to compare with findingaid doc
        ead = load_xmlobject_from_string(response.content)
        abbey = FindingAid.objects.get(eadid='abbey244')
        self.assertEqual(ead.serialize(), abbey.serialize(),
            "response content should be the full, valid XML content of the requested EAD document")

    def test_content_negotiation(self):
        url = reverse('fa:view-fa', kwargs={'id': 'raoul548'})

        # normal request 
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], "text/html; charset=utf-8", "Should return html")

        # request application/xml
        response = self.client.get(url, HTTP_ACCEPT = "application/xml")
        self.assertEqual(response['Content-Type'], "application/xml", "Should return xml")

        # request text/xml 
        response = self.client.get(url, HTTP_ACCEPT = "text/xml")
        self.assertEqual(response['Content-Type'], "application/xml", "Should return xml")


class UtilsTest(TestCase):
    exist_fixtures = {'files': [
            path.join(exist_fixture_path, 'abbey244.xml'),
    ]}

    def test_pages_to_show(self):
        paginator = Paginator(range(300), 10)
        # range of pages at the beginning
        pages = pages_to_show(paginator, 1)
        self.assertEqual(7, len(pages), "show pages returns 7 items for first page")
        self.assert_(1 in pages, "show pages includes 1 for first page")
        self.assert_(6 in pages, "show pages includes 6 for first page")

        pages = pages_to_show(paginator, 2)
        self.assert_(1 in pages, "show pages for page 2 includes 1")
        self.assert_(2 in pages, "show pages for page 2 includes 2")
        self.assert_(3 in pages, "show pages for page 2 includes 3")

        # range of pages in the middle
        pages = pages_to_show(paginator, 15)
        self.assertEqual(7, len(pages), "show pages returns 7 items for middle of page result")
        self.assert_(15 in pages, "show pages includes current page for middle of page result")
        self.assert_(12 in pages,
            "show pages includes third page before current page for middle of page result")
        self.assert_(18 in pages,
            "show pages includes third page after current page for middle of page result")

        # range of pages at the end
        pages = pages_to_show(paginator, 30)
        self.assertEqual(7, len(pages), "show pages returns 7 items for last page")
        self.assert_(30 in pages, "show pages includes last page for last page of results")
        self.assert_(24 in pages,
            "show pages includes 6 pages before last page for last page of results")

    def test_ead_lastmodified(self):
        modified = ead_lastmodified('rqst', 'abbey244')
        self.assert_(isinstance(modified, datetime),
                     "ead_lastmodified should return a datetime object")
        date_format = '%Y-%m-%d'
        expected = datetime.now().strftime(date_format)
        value = modified.strftime(date_format)
        self.assertEqual(expected, value,
                     'ead lastmodified should be today, expected %s, got %s' % (expected, value))

        # invalid eadid
        self.assertRaises(Http404, ead_lastmodified, 'rqst', 'bogusid')

        db = ExistDB()
        # preview document - load fixture to preview collection
        fullpath = path.join(settings.BASE_DIR, 'fa', 'fixtures', 'raoul548.xml')
        db.load(open(fullpath, 'r'), settings.EXISTDB_PREVIEW_COLLECTION + '/raoul548.xml',
                overwrite=True)        
        preview_modified = ead_lastmodified('rqst', 'raoul548', preview=True)
        self.assert_(isinstance(preview_modified, datetime),
                     "ead_lastmodified should return a datetime object")
        # clean up
        db.removeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/raoul548.xml')
        
    def test_ead_etag(self):
        checksum = ead_etag('rqst', 'abbey244')
        self.assert_(re.match('[0-9a-f]{40}$', checksum),
                     'ead etag should be 40-character hex checksum, got %s' % checksum)
        # invalid eadid
        self.assertRaises(Http404, ead_etag, 'rqst', 'bogusid')

    def test_collection_lastmodified(self):
        modified = collection_lastmodified('rqst')
        self.assert_(isinstance(modified, datetime),
                     "collection_lastmodified should return a datetime object")
       
        # should equal last modified of abbey244 (last document loaded)
        fa = FindingAid.objects.only('last_modified').get(eadid='abbey244')
        self.assertEqual(exist_datetime_with_timezone(fa.last_modified), modified,
            'collection last modified should be datetime of most recently modified document in collection')

        # delete something after eXist document last-modified
        sleep(1) # ensure deleted record is picked up as most recent
        Deleted(eadid='eadid', title='test deleted record', date=datetime.now()).save()
        record = Deleted.objects.get(eadid='eadid')     # retrieve datetime from DB
        modified = collection_lastmodified('rqst')
        #NOTE: THIS TEST DEPENDS ON THE LOCAL MACHINE TIME BEING SET CORRECTLY
        self.assertEqual(exist_datetime_with_timezone(record.date), modified,
            'collection last modified should be datetime of most recently deleted document in collection')
        
class FullTextFaViewsTest(TestCase):
    # test for views that require eXist full-text index
    exist_fixtures = { 'index' : exist_index_path,
                       'directory' : exist_fixture_path }

    def test_keyword_search(self):
        search_url = reverse('fa:keyword-search')
        response = self.client.get(search_url, { 'keywords' : 'raoul'})
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, search_url))

        self.assertPattern("<p[^>]*>Search results for : .*raoul.*</p>", response.content,
            msg_prefix='search results include search term')
        self.assertContains(response, "1 finding aid found",
            msg_prefix='search for "raoul" returns one finding aid')
        self.assertContains(response, reverse('fa:view-fa', kwargs={'id': 'raoul548'}),
            msg_prefix='search for raoul includes link to raoul finding aid')
        self.assertContains(response, "<div class=\"relevance\">",
            msg_prefix='search results include relevance indicator')
        self.assertContains(response, '%s?keywords=raoul' % reverse('fa:view-fa', kwargs={'id': 'raoul548'}),
            msg_prefix='link to finding aid includes search terms')

        self.assertContains(response, '<meta name="robots" content="noindex,nofollow"',
            msg_prefix="search results page includes robots directives - noindex, nofollow")

        response = self.client.get(search_url, { 'keywords' : 'family papers'})
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, search_url))
        self.assertPattern("<p[^>]*>Search results for : .*family papers.*</p>", response.content)
        self.assertContains(response, "5 finding aids found",
            msg_prefix='search for "family papers" should return 5 test finding aids')
        self.assertContains(response, "Fannie Lee Leverette scrapbooks",
            msg_prefix='search for "family papers" should include Leverette')
        self.assertPattern("Raoul .*family.* .*papers", response.content,   # exist-match highlighting
            msg_prefix='search for "family papers" should include raoul')
        self.assertPattern("Bailey and Thurman families .*papers", response.content,
            msg_prefix='search for "family papers" should include bailey')
        self.assertContains(response, "Abbey Theatre collection",
            msg_prefix='search for "family papers" should include abbey theatre')
        self.assertContains(response, "Pomerantz, Gary M.",
            msg_prefix='search for "family papers" should include pomerantz')
        self.assertContains(response, "<div class=\"relevance\">", 5,
            msg_prefix='search results return one relevance indicator for each match')
        self.assertContains(response, '%s?keywords=family+papers' % reverse('fa:view-fa', kwargs={'id': 'leverette135'}),
            msg_prefix='link to finding aid includes search terms')

        response = self.client.get(search_url, { 'keywords' : 'nonexistentshouldmatchnothing'})
        expected = 200
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, search_url))
        self.assertContains(response, "No finding aids matched",
            msg_prefix='search for nonexistent term should indicate no matches found')


    def test_view_highlighted_fa(self):
        # view a finding aid with search-term highlighting
        fa_url = reverse('fa:view-fa', kwargs={'id': 'raoul548'})
        response = self.client.get(fa_url, {'keywords': 'raoul georgia'})
        self.assertContains(response, '%s?keywords=raoul+georgia#descriptive_summary' \
                % reverse('fa:view-fa',  kwargs={'id': 'raoul548'}),
                msg_prefix="descriptive summary anchor-link includes search terms")
        self.assertContains(response, '%s?keywords=raoul+georgia' \
                % reverse('fa:series-or-index',  kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4'}),
                msg_prefix="series link includes search terms")
        self.assertContains(response, '%s?keywords=raoul+georgia' \
                % reverse('fa:series-or-index',  kwargs={'id': 'raoul548', 'series_id': 'index1'}),
                msg_prefix="index link includes search terms")
        self.assertContains(response, '%s?keywords=raoul+georgia' \
                %  reverse('fa:view-subseries', kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223',
                        'subseries_id': 'raoul548_100904'}),
                msg_prefix="subseries link includes search terms")

        self.assertContains(response, '<meta name="robots" content="noindex,nofollow"',
            msg_prefix="highlighted finding aid includes robots directives - noindex, nofollow")
        self.assertContains(response, '<link rel="canonical" href="%s"' % fa_url,
            msg_prefix="highlighted finding aid includes link to canonical finding aid url")

        # highlighting
        #print response
        self.assertContains(response, '<span class="exist-match">Raoul</span>',
                msg_prefix="search terms are highlighted on main finding aid page")
        self.assertContains(response, '<span class="exist-match">Raoul</span>, Eleanore',
                msg_prefix="search terms in control access terms are highlighted")

    def test_view_highlighted_series(self):
        # single series in a finding aid, with search-term highlighting
        # NOTE: series, subseries, and index all use the same view
        series_url = reverse('fa:series-or-index',
                    kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4'})
        response = self.client.get(series_url, {'keywords': 'raoul georgia'})
        self.assertContains(response, '%s?keywords=raoul+georgia' \
                % reverse('fa:view-fa',  kwargs={'id': 'raoul548'}),
                msg_prefix="link back to main FA page includes search terms")
        self.assertContains(response, '%s?keywords=raoul+georgia' \
                % reverse('fa:series-or-index',  kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003223'}),
                msg_prefix="link to other series includes search terms")
        self.assertContains(response, '%s?keywords=raoul+georgia' \
                % reverse('fa:series-or-index',  kwargs={'id': 'raoul548', 'series_id': 'index1'}),
                msg_prefix="index link includes search terms")
        self.assertContains(response, '%s?keywords=raoul+georgia' \
                %  reverse('fa:view-subseries', kwargs={'id': 'raoul548', 'series_id': 'raoul548_s4',
                        'subseries_id': 'raoul548_4.1'}),
                msg_prefix="subseries link includes search terms")      

        self.assertContains(response, '<meta name="robots" content="noindex,nofollow"',
            msg_prefix="highlighted finding aid series includes robots directives - noindex, nofollow")
        self.assertContains(response, '<link rel="canonical" href="%s"' % series_url,
            msg_prefix="highlighted finding aid series includes link to canonical url")

        # highlighting
        self.assertContains(response, '<span class="exist-match">Raoul</span>',
                msg_prefix="search terms are highlighted on series page")
        self.assertContains(response, 'genealogy, the <span class="exist-match">Raoul</span> mansion',
                msg_prefix="search terms in scope/content note are highlighted")
                
        # series 3 - box/folder/content
        series_url = reverse('fa:series-or-index',
                    kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003798'})
        response = self.client.get(series_url, {'keywords': 'raoul georgia'})          
        self.assertContains(response, 'W. G. <span class="exist-match">Raoul</span> estate papers',
            msg_prefix="search terms in box/folder section headings are highlighted")
        self.assertContains(response, '<span class="exist-match">Raoul</span> Heirs, Inc.',
                msg_prefix="search terms in box/folder contents are highlighted")

        # search terms not in current series
        series_url = reverse('fa:series-or-index',
                    kwargs={'id': 'raoul548', 'series_id': 'raoul548_1003798'})
        response = self.client.get(series_url, {'keywords': 'notinthistext'})
        self.assertContains(response, 'Financial and legal papers',
            msg_prefix="series without search terms is still returned normally")

    def test_view_highlighted_subseries(self):
        # single subseries in a finding aid, with search-term highlighting
        series_url = reverse('fa:view-subseries', kwargs={'id': 'raoul548',
                'series_id': 'raoul548_1003223', 'subseries_id': 'raoul548_100355'})
        response = self.client.get(series_url, {'keywords': 'raoul georgia'})
        self.assertContains(response, '<link rel="canonical" href="%s"' % series_url,
            msg_prefix="highlighted finding aid subseries includes link to canonical url")

        # highlighting
        self.assertContains(response, '<span class="exist-match">Raoul</span>',
                msg_prefix="search terms are highlighted on subseries page")
         # search terms not in current subseries
        response = self.client.get(series_url, {'keywords': 'notinthistext'})
        self.assertContains(response, 'Photographs',
            msg_prefix="subseries without search terms is still returned normally")


    def test_view_highlighted_index(self):
        # single index in a finding aid, with search-term highlighting
        index_url = reverse('fa:series-or-index',
                    kwargs={'id': 'raoul548', 'series_id': 'index1'})
        response = self.client.get(index_url, {'keywords': 'raoul georgia'})
        self.assertContains(response, '<link rel="canonical" href="%s"' % index_url,
            msg_prefix="highlighted finding aid index includes link to canonical url")

        # highlighting
        self.assertContains(response, '<span class="exist-match">Georgia</span>',
                msg_prefix="search terms are highlighted on index page")
        self.assertContains(response, '<span class="exist-match">Georgia</span> Institute of Technology',
                msg_prefix="search terms in index entry headings are highlighted")
        self.assertContains(response, 'Peacock School, Atlanta, <span class="exist-match">Georgia</span>',
                msg_prefix="search terms in index references are highlighted")
         # search terms not in index
        response = self.client.get(index_url, {'keywords': 'notinthistext'})
        self.assertContains(response, 'Index of Selected Correspondents',
            msg_prefix="index without search terms is still returned normally")


class FormatEadTestCase(DjangoTestCase):
# test ead_format template tag explicitly
    ITALICS = """<titleproper><emph render="italic">Pitts v. Freeman</emph> school desegregation case files,
1969-1993</titleproper>"""
    BOLD = """<titleproper><emph render="bold">Pitts v. Freeman</emph> school desegregation case files,
1969-1993</titleproper>"""
    TITLE = """<abstract>A submission for the magazine <title>The Smart Set</title> from
    Irish writer Oliver St. John Gogarty to author Ernest Augustus Boyd.</abstract>"""
    TITLE_EMPH = """<bibref><emph>Biographical source:</emph> "Shaw, George Bernard."
    <title>Contemporary Authors Online</title>, Gale, 2003</bibref>"""
    NESTED = """<abstract>magazine <title>The <emph render="doublequote">Smart</emph> Set</title>...</abstract>"""
    NOTRANS = """<abstract>magazine <title>The <bogus>Smart</bogus> Set</title>...</abstract>"""
    EXIST_MATCH = """<abstract>Pitts v. <exist:match xmlns:exist="http://exist.sourceforge.net/NS/exist">Freeman</exist:match>
school desegregation case files</abstract>"""

    def setUp(self):
        self.content = XmlObject(etree.fromstring(self.ITALICS))    # place-holder node
        
    def test_italics(self):
        self.content.node = etree.fromstring(self.ITALICS)
        format = format_ead(self.content)
        self.assert_('<span class="ead-italic">Pitts v. Freeman</span> school desegregation' in format,
            "render italic converted correctly to span class ead-italic")

    def test_bold(self):
        self.content.node = etree.fromstring(self.BOLD)
        format = format_ead(self.content)
        self.assert_('<span class="ead-bold">Pitts v. Freeman</span> school desegregation' in format,
            "render bold converted correctly to span class ead-bold")

    def test_title(self):
        self.content.node  = etree.fromstring(self.TITLE)
        format = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The Smart Set</span> from' in format,
            "title tag converted correctly to span class ead-title")

    def test_title_emph(self):
        self.content.node = etree.fromstring(self.TITLE_EMPH)
        format = format_ead(self.content)
        self.assert_('<em>Biographical source:</em> "Shaw, George' in format,
            "emph tag rendered correctly in section with title")
        self.assert_('<span class="ead-title">Contemporary Authors Online</span>, Gale' in format,
            "title rendered correctly in sectino with emph tag")

    def test_nested(self):
        self.content.node = etree.fromstring(self.NESTED)
        format = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The "Smart" Set</span>...' in format,
            "nested format rendered correctly")
        
    def test_notrans(self):
        self.content.node = etree.fromstring(self.NOTRANS)
        format = format_ead(self.content)
        self.assert_('magazine <span class="ead-title">The Smart Set</span>...' in format,
            "nested format rendered correctly")

    def test_exist_match(self):
        self.content.node = etree.fromstring(self.EXIST_MATCH)
        format = format_ead(self.content)
        self.assert_('Pitts v. <span class="exist-match">Freeman</span>'
            in format, 'exist:match tag converted to span for highlighting')
        
        
# test custom template tag ifurl
class IfUrlTestCase(DjangoTestCase):

    def test_ifurl(self):
        template = Template("{% load ifurl %}{% ifurl preview fa:full-fa fa:view-fa id=id %}")
        urlopts = {'id': 'docid'}
        context = RequestContext(HttpRequest(), {'preview': False, 'id': 'docid'})        
        url = template.render(context)
        self.assertEqual(reverse('fa:view-fa', kwargs=urlopts), url,
            "when condition is false, url is generated from second named url")

        context = RequestContext(HttpRequest(), {'preview': True, 'id': 'docid'})
        url = template.render(context)
        self.assertEqual(reverse('fa:full-fa', kwargs=urlopts), url,
            "when condition is true, url is generated from first named url")

    def test_ifurl_asvar(self):
        # store ifurl output in a context variable and then render it for testing
        template = Template("{% load ifurl %}{% ifurl preview fa:full-fa fa:view-fa id=id as myurl %}{{ myurl }}")
        urlopts = {'id': 'docid'}
        context = RequestContext(HttpRequest(), {'preview': False, 'id': 'docid'})
        url = template.render(context)
        self.assertEqual(reverse('fa:view-fa', kwargs=urlopts), url,
            "ifurl correctly stores resulting url in context when 'as' is specified")
