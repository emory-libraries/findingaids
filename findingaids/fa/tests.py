from os import path
from glob import glob
import re
from django.test import Client, TestCase
from django.conf import settings
from eulcore.xmlmap  import load_xmlobject_from_file
from eulcore.django.existdb.db import ExistDB
from findingaids.fa.models import FindingAid

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
        
    def test_browse_letter_list(self):
        response = self.client.get('/browse')
        self.assertEquals(response.status_code, 200)

        response = self.client.get('/browse/')
        self.assertEquals(response.status_code, 200)

        # first letters from 4 test documents
        self.assertContains(response, 'href="/browse/A"')
        self.assertContains(response, 'href="/browse/B"')
        self.assertContains(response, 'href="/browse/L"')
        self.assertContains(response, 'href="/browse/R"')
        # should not include first letters not present in the data
        self.assertContains(response, 'href="/browse/Z"', 0)

    def test_browse_by_letter(self):
        response = self.client.get('/browse/A')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'href="/view/abbey244')
        self.assertContains(response, '<p class="abstract">Collection of play scripts')
        self.assertContains(response, '2 finding aids found')
        # test pagination ?
        
        # test current letter
        # TODO regex test?  remove whitespace to test better?
        self.assertContains(response, "<li class='active'>")

        # no finding aids
        response = self.client.get('/browse/Z')
        self.assertContains(response, '<div>No finding aids found.</div>')

    def test_view_notfound(self):
        response = self.client.get('/view/nonexistent')
        self.assertEquals(response.status_code, 404)

    def test_view_simple(self):
        response = self.client.get('/view/leverette135.xml')
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
        response = self.client.get('/view/abbey244.xml')
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
        response = self.client.get('/view/raoul548.xml')
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
        response = self.client.get('/view/adams465.xml')
        self.assertEquals(response.status_code, 200)

        # record with no dsc - no container list or series
        self.assert_('Container List' not in response.content)
        self.assert_('Description of Series' not in response.content)

        # FIXME: test also not listed in top-level table of contents?