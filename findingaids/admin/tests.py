import os
import tempfile
from time import sleep
from django.test import Client
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from eulcore.django.existdb.db import ExistDB
from findingaids.admin.views import _get_recent_xml_files
from findingaids.admin.utils import check_ead

class AdminViewsTest(TestCase):
    fixtures =  ['user']
    # create temporary directory with files for testing
    # (unchanged by tests, so only doing once here instead of in setup)
    tmpdir = tempfile.mkdtemp('findingaids-recentfiles-test')
    tmpfiles = []
    for num in ['first', 'second', 'third']:
        tmpfiles.append(tempfile.NamedTemporaryFile(suffix='.xml', prefix=num+'_', dir=tmpdir))
        sleep(1)        # ensure modification times are different
    # add a non-xml file
    nonxml_tmpfile = tempfile.NamedTemporaryFile(suffix='.txt', prefix='nonxml', dir=tmpdir)

    def setUp(self):
        self.client = Client()
        # tmp dir for testing source ead files
        
        # temporarily override setting for testing
        if hasattr(settings, 'FINDINGAID_EAD_SOURCE'):
            self._stored_ead_src = settings.FINDINGAID_EAD_SOURCE
        settings.FINDINGAID_EAD_SOURCE = self.tmpdir

    def tearDown(self):
        if hasattr(self, '_stored_ead_src'):
            settings.FINDINGAID_EAD_SOURCE = self._stored_ead_src

    def test_get_recent_xml_files(self):        
        recent_xml = _get_recent_xml_files(self.tmpdir)
        filenames = [file for file, mtime in recent_xml]
        self.assertEqual(3, len(recent_xml))
        # should be in reverse order - last created first
        self.assertEqual(filenames[0], os.path.basename(self.tmpfiles[2].name))
        self.assertEqual(filenames[1], os.path.basename(self.tmpfiles[1].name))
        self.assertEqual(filenames[2], os.path.basename(self.tmpfiles[0].name))
        # non-xml file not included
        self.assert_(os.path.basename(self.nonxml_tmpfile.name) not in filenames)

        # restrict just to two - confirm only 2 are returned
        recent_xml = _get_recent_xml_files(self.tmpdir, 2)
        self.assertEqual(2, len(recent_xml))

    def test_recent_files(self):
        admin_index = reverse('admin:index')
        # note: recent files list is *currently* displayed on main admin page

        # not logged in
        response = self.client.get(admin_index)
        code = response.status_code
        expected = 302
        self.failUnlessEqual(code, expected, 'Expected %s but returned %s for %s as AnonymousUser'
                             % (expected, code, admin_index))

        # follow redirects
        response = self.client.get(admin_index, follow=True)
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_("?next=%s" % admin_index in redirect_url)
        
        # log in as an admin user
        self.client.login(username='testadmin', password='secret')
        response = self.client.get(admin_index)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(3, len(response.context['files']))
        self.assert_('error' not in response.context)
        self.assertContains(response, os.path.basename(self.tmpfiles[0].name))
        self.assertContains(response, os.path.basename(self.tmpfiles[2].name))

        # simulate configuration error
        settings.FINDINGAID_EAD_SOURCE = "/does/not/exist"
        response = self.client.get(admin_index)
        self.assert_("check config file" in response.context['error'])
        self.assertEqual(0, len(response.context['files']))

    def test_publish(self):
        self.client.login(username='testadmin', password='secret')
        # GET should just list files available to be published
        response = self.client.get('/admin/publish')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, os.path.basename(self.tmpfiles[0].name))

        # use EAD fixture dircetory to test publication
        ### TODO  - can't test this until we have fixture users
        #settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa', 'fixtures')
        #response = self.client.post('/admin/publish', {'filename' : 'abbey244.xml'})
        #print response
        #print response.status
        #print self.client.session

class UtilsTest(TestCase):
    
    def test_check_ead(self):
        # check valid EAD - no errors  -- good fixture, should pass all tests
        dbpath = settings.EXISTDB_TEST_COLLECTION + '/hartsfield588.xml'
        valid_eadfile = os.path.join(settings.BASE_DIR, 'admin', 'fixtures', 'hartsfield558.xml')
        errors = check_ead(valid_eadfile, dbpath)
        self.assertEqual(0, len(errors))

        # should cause several errors - not DTD valid, eadid, series/subseries ids missing, index id missing
        errors = check_ead(os.path.join(settings.BASE_DIR, 'admin', 'fixtures', 'hartsfield558_invalid.xml'),
                dbpath)
        self.assertNotEqual(0, len(errors))
        self.assert_("Attribute 'invalid' not declared" in errors[0])   # validation error
        self.assert_("eadid 'hartsfield558.xml' does not match expected value" in errors[1])
        self.assert_("series c01 id attribute is not set for Series 1" in errors[2])
        self.assert_("subseries c02 id attribute is not set for Subseries 6.1" in errors[3])
        self.assert_("index id attribute is not set for Index of Selected Correspondents" in errors[4])

        # eadid uniqueness check in db
        db = ExistDB()
        db.load(open(valid_eadfile), dbpath, True)
        errors = check_ead(valid_eadfile, dbpath)
        # same eadid, but present in the file that will be updated - no errors
        self.assertEqual(0, len(errors))

        # upload same file to a different path - non-unique eadid error
        db.load(open(valid_eadfile), settings.EXISTDB_TEST_COLLECTION + '/harstfield_other.xml', True)
        errors = check_ead(valid_eadfile, dbpath)
        self.assertEqual(1, len(errors))
        self.assert_("Database already contains 2 instances of eadid" in errors[0])

        # remove version with correct path to test single conflicting eadid
        db.removeDocument(dbpath)
        errors = check_ead(valid_eadfile, dbpath)
        self.assertEqual(1, len(errors))
        self.assert_("Database contains eadid 'hartsfield558' in a different document" in errors[0])
        db.removeDocument(settings.EXISTDB_TEST_COLLECTION + '/harstfield_other.xml')

