import os
import tempfile
from time import sleep
from shutil import rmtree

from django.test import Client, TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator

from eulcore.django.existdb.db import ExistDB
from eulcore.django.test import TestCase
from eulcore.xmlmap.core import load_xmlobject_from_file

from findingaids.fa_admin.views import _get_recent_xml_files, _pages_to_show
from findingaids.fa_admin.utils import check_ead, clean_ead
from findingaids.fa.models import FindingAid


class AdminViewsTest(TestCase):
    fixtures =  ['user']
    admin_credentials = {'username': 'testadmin', 'password': 'secret'}

    # create temporary dirctory with files for testing
    # (unchanged by tests, so only doing once here instead of in setup)
    tmpdir = tempfile.mkdtemp('findingaids-recentfiles-test')
    tmpfiles = []
    for num in ['first', 'second', 'third']:
        tmpfiles.append(tempfile.NamedTemporaryFile(suffix='.xml', prefix=num+'_', dir=tmpdir))
        sleep(1)        # ensure modification times are different
    # add a non-xml file
    nonxml_tmpfile = tempfile.NamedTemporaryFile(suffix='.txt', prefix='nonxml', dir=tmpdir)

    db = ExistDB()

    def setUp(self):
        self.client = Client()

        # create temporary directory with files for testing
        # - turning off auto-delete so directory and files can be easily cleaned up
        self.tmpdir = tempfile.mkdtemp('findingaids-recentfiles-test')
        self.tmpfiles = []
        for num in ['first', 'second', 'third']:
            self.tmpfiles.append(tempfile.NamedTemporaryFile(suffix='.xml',
                    prefix=num+'_', dir=self.tmpdir, delete=False))
            sleep(1)        # ensure modification times are different
        # add a non-xml file
        self.nonxml_tmpfile = tempfile.NamedTemporaryFile(suffix='.txt',
                    prefix='nonxml', dir=self.tmpdir, delete=False)
        
        # temporarily override setting for testing
        if hasattr(settings, 'FINDINGAID_EAD_SOURCE'):
            self._stored_ead_src = settings.FINDINGAID_EAD_SOURCE
        settings.FINDINGAID_EAD_SOURCE = self.tmpdir

    def tearDown(self):
        if hasattr(self, '_stored_ead_src'):
            settings.FINDINGAID_EAD_SOURCE = self._stored_ead_src
            
        # clean up temp files & dir
        rmtree(self.tmpdir)

    def test_recent_files(self):
        admin_index = reverse('fa-admin:index')
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
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as admin'
                             % (expected, code, admin_index))
        self.assertEqual(3, len(response.context['files'].object_list))
        self.assert_(response.context['show_pages'], "file list view includes list of pages to show")
        self.assertEqual(None, response.context['error'],
                "correctly configured file list view has no error messages")
        self.assertContains(response, os.path.basename(self.tmpfiles[0].name))
        self.assertContains(response, os.path.basename(self.tmpfiles[2].name))
        # file list contains buttons to publish documents
        publish_url = reverse('fa-admin:publish-ead')
        self.assertContains(response, '<form action="%s" method="post"' % publish_url)
        self.assertContains(response, '<button type="submit" name="filename" value="%s" '
                % os.path.basename(self.tmpfiles[0].name))
        # file list contains buttons to prnvenw documents
        preview_url = reverse('fa-admin:preview-ead')
        self.assertContains(response, '<form action="%s" method="post"' % preview_url)
        self.assertContains(response, '<button type="submit" name="filename" value="%s" '
                % os.path.basename(self.tmpfiles[0].name), 2)
        # file list contains link to clean documents
        clean_url = reverse('fa-admin:cleaned-ead-about', args=[os.path.basename(self.tmpfiles[0].name)])
        self.assertContains(response, '<a href="%s">CLEAN</a>' % clean_url)

        # simulate configuration error
        settings.FINDINGAID_EAD_SOURCE = "/does/not/exist"
        response = self.client.get(admin_index)
        self.assert_("check config file" in response.context['error'])
        self.assertEqual(0, len(response.context['files'].object_list))

    def test_publish(self):
        publish_url = reverse('fa-admin:publish-ead')
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
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        response = self.client.post(publish_url, {'filename' : filename}, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, following redirects) as admin user'
                             % (expected, code, publish_url))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)       
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
        self.assertContains(response, "No declaration for attribute invalid")   # DTD validation error
        self.assertContains(response, "series c01 id attribute is not set")
        self.assertContains(response, "index id attribute is not set")
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/hartsfield588_invalid.xml')
        self.assertEqual({}, docinfo)   # invalid document not loaded to exist

        # attempt to publish non-well-formed xml - display errors
        response = self.client.post(publish_url, {'filename' : 'badlyformed.xml'})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, not well-formed xml) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, "Could not publish")
        self.assertContains(response, "Unescaped &#39;&lt;&#39; not allowed in attributes values",
            msg_prefix="syntax error detail for badly formed XML displays")


    def test_preview(self):
        preview_url = reverse('fa-admin:preview-ead')
        self.client.login(**self.admin_credentials)
        
        # use fixture directory to test preview
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        response = self.client.post(preview_url, {'filename' : filename})
        # NOTE: django testclient doesn't seem to load preview versions correctly
        code = response.status_code
        preview_docurl = reverse('fa-admin:preview:view-fa', kwargs={'id': 'hartsfield558'})
        self.assert_(preview_docurl in response['Location'])
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
                             % (expected, code, preview_url))
        # because preview response fails, can't check preview page (?)
        #self.assertContains(response, "Successfully loaded")
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)
        # confirm that document was actually saved to exist
        self.assertEqual(docinfo['name'], settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)

        # GET should just list files available for preview
        response = self.client.get(preview_url)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (GET) as admin user'
                             % (expected, code, preview_url))
        self.assertContains(response, "Hartsfield, William Berry",
            msg_prefix="preview summary should list title of document loaded for preview")
        self.assertContains(response, reverse('fa-admin:preview:view-fa', kwargs={'id': 'hartsfield558'}),
            msg_prefix="preview summary should link to preview page for document loaded to preview")
        self.assertContains(response, 'last modified: 0 minutes ago',
            msg_prefix="preview summary listing includes modification time")
            
        # clean up
        self.db.removeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)

        # preview invalid document - should display errors
        response = self.client.post(preview_url, {'filename' : 'hartsfield558_invalid.xml'})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, invalid document) as admin user'
                             % (expected, code, preview_url))
        self.assertContains(response, "Could not preview")
        self.assertContains(response, "No declaration for attribute invalid")   # DTD validation error
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/hartsfield588_invalid.xml')
        self.assertEqual({}, docinfo)   # invalid document not loaded to exist

    def test_publish_from_preview(self):
        # test publishing a document that has been loaded for preview
        publish_url = reverse('fa-admin:publish-ead')
        self.client.login(**self.admin_credentials)

        # load a file to preview to test
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        response = self.client.post(reverse('fa-admin:preview-ead'), {'filename' : filename})

        # publish the preview file
        response =  self.client.post(publish_url, {'preview_id': 'hartsfield558'}, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, following redirects) as admin user'
                             % (expected, code, publish_url))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, "Successfully added",     # NOTE: this could be 'updated' if a previous test failed
            msg_prefix='publication success message displays')
        self.assertContains(response, 'href="%s"' % reverse('fa:view-fa', kwargs={'id': 'hartsfield558'}),
            msg_prefix='success message links to published document')
        self.assertContains(response, 'William Berry Hartsfield papers',
            msg_prefix='success message includes unit title of published document')

        # confirm that document was moved to main collection
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        self.assertEqual(docinfo['name'], settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        # confirm that document is no longer in preview collection
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)        
        self.assertEqual({}, docinfo)

        # attempt to publish a document NOT loaded to preview
        response =  self.client.post(publish_url, {'preview_id': 'bogus345'}, follow=True)
        messages = response.context['messages']
        self.assertContains(response, 'Publish failed. Could not retrieve',
            msg_prefix='error message displayed when attempting to publish a document not in preview')

        # clean up
        self.db.removeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)


    def test_login_admin(self):
        admin_index = reverse('fa-admin:index')
        # Test admin account can login
        response = self.client.post('/accounts/login/', {'username': 'testadmin', 'password': 'secret'})
        response = self.client.get(admin_index)
        self.assertContains(response, '<p>You are logged in as,')
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as admin' % (expected, code, admin_index))
        
    def test_login_staff(self):
        admin_index = reverse('fa-admin:index')
        staff = User.objects.create_user('staffmember', 'staff.member@emory.edu', 'staffpassword')
        staff.is_staff = True
        staff.save()
        # Test staff account can login
        response = self.client.post('/accounts/login/', {'username': 'staffmember', 'password': 'staffpassword'})
        response = self.client.get(admin_index)
        self.assertContains(response, '<p>You are logged in as,')
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as admin' % (expected, code, admin_index))

    def test_login_non_existent(self):
        admin_index = reverse('fa-admin:index')    
        # Test a none existent account cannot login
        response = self.client.post('/accounts/login/', {'username': 'non_existent', 'password': 'whatever'})
        self.assertContains(response, """<p>Your username and password didn't match. Please try again.</p>""")
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, admin_index))
        
    def test_logout(self):
        admin_index = reverse('fa-admin:index')
        # Test admin account can login
        response = self.client.post('/accounts/login/', {'username': 'testadmin', 'password': 'secret'})
        response = self.client.get('/admin/')
        self.assertContains(response, '<p>You are logged in as,')
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, admin_index))
        response = self.client.get('/admin/logout')
        response = self.client.get('/accounts/login/')
        self.assertContains(response, '<li class="success">You have logged out of finding aids.</li>')
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, admin_index))

    def test_list_staff(self):
        admin_index = reverse('fa-admin:index')
        # Test admin account can login
        self.client.login(**self.admin_credentials)
        response = self.client.get('/admin/accounts/')
        self.assertContains(response, "Current users")
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, admin_index))

    def test_edit_user(self):
        admin_index = reverse('fa-admin:index')
        # Test admin account can login
        self.client.login(**self.admin_credentials)
        user = User.objects.create_user('test', 'test@emory.edu', 'testpassword')
        user.is_staff = True
        user.save()
        response = self.client.get('/admin/accounts/user/%d/' % user.id)
        self.assertContains(response, "<p>Please edit the user settings...</p>")
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, admin_index))

    def test_cleaned_ead(self):
         # use fixture directory to test publication
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')        
        
        cleaned_xml = reverse('fa-admin:cleaned-ead', args=[filename])
        cleaned_summary = reverse('fa-admin:cleaned-ead-about', args=[filename])
        cleaned_diff = reverse('fa-admin:cleaned-ead-diff', args=[filename])
        
        self.client.login(**self.admin_credentials)
        response = self.client.get(cleaned_summary)
        
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, cleaned_summary))
        self.assert_(response.context['changes'])
                        
        self.assertContains(response, 'Cleaned EAD for %s' % filename)
        self.assertContains(response, 'View file differences line by line')
        self.assertContains(response, cleaned_diff,
                            msg_prefix="cleaned EAD summary should link to line-by-line diff")
        self.assertPattern('<p class="removed".*>-.*c01.*id=.*s1', response.content)
        self.assertPattern('<p class="added".*>+.*c01.*id=.*hartsfield558_series1.*', response.content)
        self.assertContains(response, cleaned_xml,
                            msg_prefix="cleaned EAD summary should link to xml download")

        response = self.client.get(cleaned_diff)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, cleaned_diff))
        # output is generated by difflib; just testing that response has content
        self.assertContains(response, '<table')

        response = self.client.get(cleaned_xml)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, cleaned_xml))
        expected = 'application/xml'
        self.assertEqual(response['Content-Type'], expected, "Expected '%s' but returned '%s' for %s mimetype" % \
                        (expected, response['Content-Type'], cleaned_xml))
        self.assertEqual(response['Content-Disposition'], "attachment; filename=%s" % filename)
        self.assertContains(response, "<!DOCTYPE ead PUBLIC",
                    msg_prefix="response does not lose doctype declaration from original xml")
        self.assertContains(response, 'hartsfield558</eadid>')
        self.assertContains(response, '<c01 level="series" id="hartsfield558_series1"')
        self.assertContains(response, '<c02 level="subseries" id="hartsfield558_subseries6.1"')
        self.assertContains(response, '<index id="hartsfield558_index1">')

        # clean an ead that doesn't need any changes
        filename = 'abbey244.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa', 'fixtures')

        cleaned_summary = reverse('fa-admin:cleaned-ead-about', args=[filename])
        response = self.client.get(cleaned_summary, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (following redirects, clean EAD)'
                             % (expected, code, cleaned_summary))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (clean EAD)'
                             % (expected, code, cleaned_summary))
        self.assertContains(response, "No changes made to <b>%s</b>" % filename)

    def test_clean_badlyformedxml(self):
        # use fixture directory to test publication
        filename = 'badlyformed.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')

        cleaned_xml = reverse('fa-admin:cleaned-ead', args=[filename])
        cleaned_summary = reverse('fa-admin:cleaned-ead-about', args=[filename])
        cleaned_diff = reverse('fa-admin:cleaned-ead-diff', args=[filename])

        self.client.login(**self.admin_credentials)
        response = self.client.get(cleaned_xml)
        expected = 500
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s (non-well-formed xml)' % \
                        (expected, response.status_code, cleaned_summary))

        response = self.client.get(cleaned_summary)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, cleaned_summary))

        self.assertContains(response, 'Could not load document',
                msg_prefix='error loading document displayed')
        self.assertContains(response, 'not allowed in attributes',
                msg_prefix='xml syntax error displayed')
        self.assertNotContains(response, cleaned_diff,
                msg_prefix="cleaned summary for badly formed xml should NOT link to line-by-line diff")
        self.assertNotContains(response, cleaned_xml,
                msg_prefix="cleaned summary for badly formed xml should NOT link to xml for download")
        

    # tests for view helper functions

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


    def test_pages_to_show(self):
        paginator = Paginator(range(300), 10)
        # range of pages at the beginning
        pages = _pages_to_show(paginator, 1)
        self.assertEqual(7, len(pages), "show pages returns 7 items for first page")
        self.assert_(1 in pages, "show pages includes 1 for first page")
        self.assert_(6 in pages, "show pages includes 6 for first page")

        # range of pages in the middle
        pages = _pages_to_show(paginator, 15)
        self.assertEqual(7, len(pages), "show pages returns 7 items for middle of page result")
        self.assert_(15 in pages, "show pages includes current page for middle of page result")
        self.assert_(11 in pages,
            "show pages includes third page before current page for middle of page result")
        self.assert_(18 in pages,
            "show pages includes third page after current page for middle of page result")

        # range of pages at the end
        pages = _pages_to_show(paginator, 30)
        self.assertEqual(7, len(pages), "show pages returns 7 items for last page")
        self.assert_(30 in pages, "show pages includes last page for last page of results")
        self.assert_(23 in pages,
            "show pages includes 7 pages before last page for last page of results")

    def test_list_published(self):
        # Test admin account can login
        self.client.login(**self.admin_credentials)
        list_published_url = reverse('fa-admin:list_published')
        response = self.client.get(list_published_url)
        self.assertContains(response, "Published Finding Aids")
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as ad,oe' % (expected, code, list_published_url))

class UtilsTest(TestCase):
    db = ExistDB()
    
    def test_check_ead(self):
        # check valid EAD - no errors  -- good fixture, should pass all tests
        dbpath = settings.EXISTDB_TEST_COLLECTION + '/hartsfield588.xml'
        valid_eadfile = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558.xml')
        errors = check_ead(valid_eadfile, dbpath)
        self.assertEqual(0, len(errors))

        # should cause several errors - not DTD valid, eadid, series/subseries ids missing, index id missing
        errors = check_ead(os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558_invalid.xml'),
                dbpath)
        self.assertNotEqual(0, len(errors))
        self.assert_("No declaration for attribute invalid" in str(errors[0]))   # validation error
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

    def test_clean_ead(self):
        # ead with series/subseries, and index
        eadfile = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead = clean_ead(ead, eadfile)
        self.assert_(isinstance(ead, FindingAid), "clean_ead should return an instance of FindingAid")
        self.assertEqual(u'hartsfield558', ead.eadid)
        self.assertEqual(u'hartsfield558_series1', ead.dsc.c[0].id)
        self.assertEqual(u'hartsfield558_subseries6.1', ead.dsc.c[5].c[0].id)
        self.assertEqual(u'hartsfield558_index1', ead.archdesc.index[0].id)

        # ead with no series
        eadfile = os.path.join(settings.BASE_DIR, 'fa', 'fixtures', 'pittsfreeman1036.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead = clean_ead(ead, eadfile)
        self.assert_(isinstance(ead, FindingAid), "clean_ead should return an instance of FindingAid")
        self.assertEqual(u'pittsfreeman1036', ead.eadid)

        # series with no unitid
        eadfile = os.path.join(settings.BASE_DIR, 'fa', 'fixtures', 'raoul548.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead = clean_ead(ead, eadfile)
        self.assertEqual(u'raoul548_series3', ead.dsc.c[2].id)


