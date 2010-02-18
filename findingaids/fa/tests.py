from os import path
from glob import glob
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
        # test pagination ?
        
        # test current letter
        # TODO regex test?  remove whitespace to test better?
        self.assertContains(response, "<li class='active'>")

        # no finding aids
        response = self.client.get('/browse/Z')
        self.assertContains(response, '<div>No finding aids found.</div>')

