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
    admin_credentials = {'username': 'testadmin', 'password': 'secret'}
    non_existent_credentials = {'username': 'nonexistent', 'password': 'whatever'}

    db = ExistDB()
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
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as AnonymousUser'
                             % (expected, code, admin_index))

        # follow redirects
        response = self.client.get(admin_index, follow=True)
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_("?next=%s" % admin_index in redirect_url)
        
        # log in as an admin user
        self.client.login(**self.admin_credentials)
        response = self.client.get(admin_index)
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe'
                             % (expected, code, admin_index))
        self.assertEqual(3, len(response.context['files']))
        self.assert_('error' not in response.context)
        self.assertContains(response, os.path.basename(self.tmpfiles[0].name))
        self.assertContains(response, os.path.basename(self.tmpfiles[2].name))
        # file list contains buttons to publish documents
        publish_url = reverse('admin:publish-ead')
        self.assertContains(response, '<form action="%s" method="post"' % publish_url)
        self.assertContains(response, '<button type="submit" name="filename" value="%s" '
                % os.path.basename(self.tmpfiles[0].name))

        # simulate configuration error
        settings.FINDINGAID_EAD_SOURCE = "/does/not/exist"
        response = self.client.get(admin_index)
        self.assert_("check config file" in response.context['error'])
        self.assertEqual(0, len(response.context['files']))

    def test_publish(self):
        publish_url = reverse('admin:publish-ead')
        self.client.login(**self.admin_credentials)
        # GET should just list files available to be published
        response = self.client.get(publish_url)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (GET) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, os.path.basename(self.tmpfiles[0].name))

        # use fixture directory to test publication
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'admin', 'fixtures')
        response = self.client.post(publish_url, {'filename' : filename}, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, following redirects) as admin user'
                             % (expected, code, publish_url))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('admin:index') in redirect_url)       
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, "Successfully added")
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        # confirm that document was actually saved to exist
        self.assertEqual(docinfo['name'], settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        self.db.removeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)

        # publish invalid document - should display errors
        response = self.client.post(publish_url, {'filename' : 'hartsfield558_invalid.xml'})
        code = response.status_code
        expected = 200 
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, invalid document) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, "Could not publish")
        self.assertContains(response, "not declared")   # DTD validation error
        self.assertContains(response, "series c01 id attribute is not set")
        self.assertContains(response, "index id attribute is not set")
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/hartsfield588_invalid.xml')
        self.assertEqual({}, docinfo)   # invalid document not loaded to exist


    def test_login_admin(self):
        admin_index = reverse('admin:index')

        # Test admin account can login
        self.client.login(**self.admin_credentials)
        response = self.client.get(admin_index)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '''You are now logged into the Finding Aids site.</p>''')
        code = response.status_code
        print response
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, admin_index))
  
    def test_login_non_existent(self):
        admin_index = reverse('admin:index')    
        # Test a none existent account cannot login
        self.client.login(**self.non_existent_credentials)
        response = self.client.get('/accounts/login/')
        self.assertContains(response, '''<form method="post" action="/accounts/login/">''')
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, admin_index))


class UtilsTest(TestCase):
    db = ExistDB()
    
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

        # eadid uniqueness check in exist
        self.db.load(open(valid_eadfile), dbpath, True)
        errors = check_ead(valid_eadfile, dbpath)
        # same eadid, but present in the file that will be updated - no errors
        self.assertEqual(0, len(errors))

        # upload same file to a different path - non-unique eadid error
        self.db.load(open(valid_eadfile), settings.EXISTDB_TEST_COLLECTION + '/hartsfield_other.xml', True)
        errors = check_ead(valid_eadfile, dbpath)
        self.assertEqual(1, len(errors))
        self.assert_("Database already contains 2 instances of eadid" in errors[0])

        # remove version with correct path to test single conflicting eadid
        self.db.removeDocument(dbpath)
        errors = check_ead(valid_eadfile, dbpath)
        self.assertEqual(1, len(errors))
        self.assert_("Database contains eadid 'hartsfield558' in a different document" in errors[0])
        self.db.removeDocument(settings.EXISTDB_TEST_COLLECTION + '/hartsfield_other.xml')

