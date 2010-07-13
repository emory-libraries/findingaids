import os
import tempfile
from time import sleep
from shutil import rmtree

from django.test import Client, TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from eulcore.django.existdb.db import ExistDB, ExistDBException
from eulcore.django.test import TestCase
from eulcore.xmlmap.core import load_xmlobject_from_file

from findingaids.fa_admin import tasks, views
from findingaids.fa_admin.models import TaskResult
from findingaids.fa_admin.views import _get_recent_xml_files
from findingaids.fa_admin.utils import check_ead, check_eadxml, clean_ead
from findingaids.fa.models import FindingAid, Deleted
from findingaids.fa.urls import TITLE_LETTERS


### unit tests for findingaids.fa_admin.views

# note: tests for publish view are in a separate test case because
# publish makes use of a celery task, which requires additional setup for testing

class BaseAdminViewsTest(TestCase):
    "Base TestCase for admin views tests.  Common setup/teardown for admin view tests."
    fixtures =  ['user']
    credentials = {'superuser': {'username': 'testadmin', 'password': 'secret'},
                   'admin': {'username': 'marbl', 'password': 'marbl'},
                   'no_perms': {'username': 'peon', 'password': 'peon'},
    }    
    exist_fixtures = {'files': [
            os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558.xml'),
    ]}
 
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

        # save the exist collection configs for restoring
        # (some tests changes to simulate an eXist save error)
        self.real_collection = settings.EXISTDB_ROOT_COLLECTION
        self.preview_collection = settings.EXISTDB_PREVIEW_COLLECTION

    def tearDown(self):
        if hasattr(self, '_stored_ead_src'):
            settings.FINDINGAID_EAD_SOURCE = self._stored_ead_src

        # clean up temp files & dir
        rmtree(self.tmpdir)

        # restore existdb collections
        settings.EXISTDB_ROOT_COLLECTION = self.real_collection
        settings.EXISTDB_PREVIEW_COLLECTION = self.preview_collection

class AdminViewsTest(BaseAdminViewsTest):

    def test_index(self):
        admin_index = reverse('fa-admin:index')

        # user who can't do anything
        self.client.login(**self.credentials['no_perms'])
        response = self.client.get(admin_index)
        self.assertContains(response, "You don't have permission to do anything",
            msg_prefix='response for user with no permissions includes appropriate message')
        self.assertContains(response, reverse('fa-admin:list-published'), 0,
            msg_prefix='response for user with no permissions does not include link to published docs')
        self.assertContains(response, reverse('fa-admin:preview-ead'), 0,
            msg_prefix='response for user with no permissions does not include link to preview docs')
        self.assertContains(response, 'href="%s"' % reverse('fa-admin:list-staff'), 0,
            msg_prefix='response for user with no permissions does not include link to list/edit staff')
        self.assertContains(response, reverse('admin:index'), 0,
            msg_prefix='response for user with no permissions does not include link to django db admin')
            
        # user with limited permissions - in findingaid group
        self.client.login(**self.credentials['admin'])
        response = self.client.get(admin_index)
        self.assertContains(response, reverse('fa-admin:list-published'), 
            msg_prefix='response for FA admin includes link to published docs')
        self.assertContains(response, reverse('fa-admin:preview-ead'),
            msg_prefix='response for FA admin includes link to preview docs')
        self.assertContains(response, 'href="%s"' % reverse('fa-admin:list-staff'), 0,
            msg_prefix='response for (non super) FA admin does not include link to list/edit staff')
        self.assertContains(response, reverse('admin:index'), 0,
            msg_prefix='response for (non super) FA admin does not include link to django db admin')

        # superuser
        self.client.login(**self.credentials['superuser'])
        response = self.client.get(admin_index)
        self.assertContains(response, 'href="%s"' % reverse('fa-admin:list-staff'),
            msg_prefix='response for superuser includes link to list/edit staff')
        self.assertContains(response, reverse('admin:index'),
            msg_prefix='response for superuser includes link to django db admin')

    def test_recent_files(self):
        admin_index = reverse('fa-admin:index')
        # note: recent files list is currently displayed on main admin page

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
        self.client.login(**self.credentials['admin'])
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
        # file list contains buttons to preview documents
        preview_url = reverse('fa-admin:preview-ead')
        self.assertContains(response, '<form action="%s" method="post"' % preview_url)
        self.assertContains(response, '<button type="submit" name="filename" value="%s" '
                % os.path.basename(self.tmpfiles[0].name), 2)
        # file list contains link to clean documents
        clean_url = reverse('fa-admin:cleaned-ead-about', args=[os.path.basename(self.tmpfiles[0].name)])
        self.assertContains(response, '<a href="%s">CLEAN</a>' % clean_url)
        # contains pagination
        self.assertPattern('Pages:\s*1', response.content)

        # simulate configuration error
        settings.FINDINGAID_EAD_SOURCE = "/does/not/exist"
        response = self.client.get(admin_index)
        self.assert_("check config file" in response.context['error'])
        self.assertEqual(0, len(response.context['files'].object_list))

    def test_preview(self):
        preview_url = reverse('fa-admin:preview-ead')
        self.client.login(**self.credentials['admin'])
        
        # use fixture directory to test preview
        filename = 'hartsfield558.xml'
        eadid = 'hartsfield558'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        response = self.client.post(preview_url, {'filename' : filename},
                follow=True) # follow redirect so we can inspect message on response
        (redirect_url, code) = response.redirect_chain[0]
        preview_docurl = reverse('fa-admin:preview:view-fa', kwargs={'id': eadid})
        self.assert_(preview_docurl in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
                             % (expected, code, preview_url))
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assert_("Successfully loaded" in messages[0],
                "success message present in response context")
            
        # confirm that document was actually saved to exist
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)        
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
            
        # preview page should include publish form for users with permission to publish
        preview_fa_url = reverse('fa-admin:preview:view-fa', kwargs={'id': eadid})
        response = self.client.get(preview_fa_url)
        self.assertContains(response,
                '<form id="preview-publish" action="%s" method="post"' % reverse('fa-admin:publish-ead'),
                msg_prefix="preview page includes publish form")
        publish_submit = '<button type="submit" name="preview_id" value="%s">PUBLISH' % eadid
        self.assertContains(response, publish_submit,
                msg_prefix="publish form submit button has document eadid for value")


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
        self.assertContains(response, "Additional Instructions",
                msg_prefix="error page displays instructions & next steps to user")

        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/hartsfield558_invalid.xml')
        self.assertEqual({}, docinfo, "invalid xml document not loaded to exist preview")


        # exist save error should be caught & handled gracefully
        # - force an error by setting preview collection to a non-existent collection
        settings.EXISTDB_PREVIEW_COLLECTION = "/bogus/doesntexist"
        response = self.client.post(preview_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not preview")
        self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_PREVIEW_COLLECTION)     
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")
        
    def test_logout(self):
        admin_logout = reverse('fa-admin:logout')
        # log in as admin user to test logging out
        self.client.login(**self.credentials['admin'])        
        response = self.client.get(admin_logout, follow=True)
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assert_('You are now logged out' in messages[0])

    def test_list_staff(self):
        list_staff = reverse('fa-admin:list-staff')
        # test as an admin with permissions to edit accounts
        self.client.login(**self.credentials['superuser'])
        response = self.client.get(list_staff)
        self.assertContains(response, "Current users")
        # should list users from fixture
        self.assertContains(response, "marbl")
        self.assertContains(response, "peon")

    def test_edit_user(self):
        edit_user = reverse('fa-admin:edit-user', args=[2]) # edit 2nd user fixture
        # Test as an admin with permission to edit users
        self.client.login(**self.credentials['superuser'])
        user = User.objects.create_user('test', 'test@emory.edu', 'testpassword')
        user.is_staff = True
        user.save()
        response = self.client.get(edit_user)
        self.assertContains(response, "Edit the user account")
        
    def test_cleaned_ead(self):
         # use fixture directory to test publication
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')        
        
        cleaned_xml = reverse('fa-admin:cleaned-ead', args=[filename])
        cleaned_summary = reverse('fa-admin:cleaned-ead-about', args=[filename])
        cleaned_diff = reverse('fa-admin:cleaned-ead-diff', args=[filename])
        
        self.client.login(**self.credentials['admin'])
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

        self.client.login(**self.credentials['admin'])
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


    def test_list_published(self):
        # login to test admin-only view
        self.client.login(**self.credentials['admin'])

        list_published_url = reverse('fa-admin:list-published')
        response = self.client.get(list_published_url)
        self.assertContains(response, "Published Finding Aids")

        fa = response.context['findingaids']
        self.assert_(fa,"findingaids is set in response context")
        self.assertEqual(fa.object_list[0].eadid, 'hartsfield558',
            "fixture document is included in findingaids object list")                
        self.assertPattern('Pages:\s*1', response.content,
            "response contains pagination")

    def test_delete_ead(self):
        # login as admin to test admin-only feature
        self.client.login(**self.credentials['admin'])

        eadid = 'hartsfield558'
        delete_url = reverse('fa-admin:delete-ead', kwargs={'id': eadid})
        # GET - should display delete form with eadid & title from document
        response = self.client.get(delete_url)
        self.assertContains(response, '<input name="eadid" value="%s"' % eadid)
        self.assertContains(response, 'id="id_title" value="William Berry Hartsfield papers, circa 1860s-1983"')

        # POST form data to trigger a deletion
        title, note = 'William Berry Hartsfield papers', 'Moved to another archive.'
        response = self.client.post(delete_url, {'eadid': eadid, 'title': title,
                                    'note' : note, 'date': '2010-07-01 15:01:20'}, follow=True)
        # on success:
        # - the document should have been removed from eXist
        self.assertFalse(self.db.hasDocument('%s/%s.xml' % (settings.EXISTDB_TEST_COLLECTION, eadid)),
            "document should no longer be present in eXist collection after delete_ead")
        # - a Deleted db record should have been created with posted data
        deleted_info = Deleted.objects.get(eadid=eadid)
        self.assertEqual(eadid, deleted_info.eadid, "deleted record has correct eadid")
        self.assertEqual(title, deleted_info.title, "deleted record has correct ead title")
        self.assertEqual(note, deleted_info.note, "deleted record has posted note")
        # - the user should be redirected with a success message
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(redirect_url.endswith(reverse('fa-admin:list-published')),
            "response redirects to list of published documents")
        expected = 303      # redirect - see other
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST)'
                             % (expected, code, delete_url))
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assert_('Successfully removed <b>%s</b>.' % eadid in messages[0],
                "delete success message is set in response context")


        # test for expected failures for a non-existent eadid
        eadid = 'bogus-id'
        delete_nonexistent = reverse('fa-admin:delete-ead', kwargs={'id': eadid})
        # GET - attempt to load form to delete an ead not present in eXist db
        response = self.client.get(delete_nonexistent, follow=True)
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assertEqual("Error: could not retrieve <b>%s</b> for deletion." \
                % eadid, messages[0],
                "'not found' message set in response context when attempting to " +
                " GET delete form for a nonexistent eadid")
        # POST - attempt to actually delete an ead that isn't in eXist        
        response = self.client.post(delete_nonexistent, {'eadid': eadid, 'title': title,
                                                'note' : note}, follow=True)
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assertEqual("Error: could not retrieve <b>%s</b> for deletion." \
                % eadid, messages[0],
                "'not found' message set in response context when attempting to " +
                "POST delete form for a nonexistent eadid")

        # FIXME: not sure how to trigger or simulate the error case where the
        # finding aid is loaded from eXist but actual deletion fails...

    def test_redelete(self):
        # test deleting when there is already an existing deleted record in the DB
        # (e.g., document was published, deleted, re-published, and now being deleted again)
        # - update existing delete_info with new values to simplify testing
        
        self.client.login(**self.credentials['admin'])
        eadid = 'hartsfield558'
        delete_url = reverse('fa-admin:delete-ead', kwargs={'id': eadid})
        
        title, note = 'Deleted EAD record', 'removed because of foo'
        Deleted(eadid=eadid, title=title, note=note).save()

        # GET: form should display info from existing Deleted record
        response = self.client.get(delete_url)
        self.assertContains(response, 'id="id_title" value="William Berry Hartsfield papers',
            msg_prefix="edit form contains title from Finding Aid (overrides title from DB)")
        self.assertContains(response, '%s</textarea>' % note,
            msg_prefix="edit form contains notes from previous deletion")
        # POST form data to trigger a deletion and update deleted record
        new_title, new_note = 'William Berry Hartsfield papers', 'Moved to another archive.'
        new_date = '2011-08-09 15:01:20'
        response = self.client.post(delete_url, {'eadid': eadid, 'title': new_title,
                                    'note' : new_note, 'date': new_date }, follow=True)
        # *existing* deleted DB record should be updated with posted data
        deleted_info = Deleted.objects.get(eadid=eadid)
        self.assertEqual(new_title, deleted_info.title)
        self.assertEqual(new_note, deleted_info.note)
        

 
# unit tests for views that make use of celery tasks (additional setup required)

# in test mode, celery task returns an EagerResult with no task id
# intercept the result from the real task and add a task id for testing
class Mock_reload_pdf:
    def delay(self, eadid):        
        result = tasks.reload_cached_pdf.delay(eadid)
        result.task_id = "test-task-id"
        return result       
        

class CeleryAdminViewsTest(BaseAdminViewsTest):
   
    def setUp(self):
        super(CeleryAdminViewsTest, self).setUp()
        _celerytest_setUp(self)

        # swap out celery task in views with our mock version
        self.real_reload = views.reload_cached_pdf
        views.reload_cached_pdf = Mock_reload_pdf()

    def tearDown(self):
        super(CeleryAdminViewsTest, self).tearDown()
        _celerytest_tearDown(self)

        # restore the real celery task
        views.reload_cached_pdf = self.real_reload

    def test_publish(self):       
        publish_url = reverse('fa-admin:publish-ead')
        self.client.login(**self.credentials['admin'])
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

        # convert mesages into an easier format to test
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assert_("Successfully updated" in messages[0], "success message set in context")

        # confirm that document was actually saved to exist
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)        
        self.assertEqual(docinfo['name'], settings.EXISTDB_TEST_COLLECTION + '/' + filename)

        task = TaskResult.objects.get(eadid='hartsfield558')
        self.assert_(isinstance(task, TaskResult), 
            "TaskResult was created in db for pdf reload after successful publish")

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
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/hartsfield558_invalid.xml')
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

        # force an exist save error by setting collection to a non-existent collection        
        settings.EXISTDB_ROOT_COLLECTION = "/bogus/doesntexist"
        response = self.client.post(publish_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not publish",
                msg_prefix="exist save error on publish displays error to user")
        self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_ROOT_COLLECTION,
                msg_prefix="specific exist save error displayed to user")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

    def test_publish_from_preview(self):
        # test publishing a document that has been loaded for preview
        publish_url = reverse('fa-admin:publish-ead')
        self.client.login(**self.credentials['admin'])

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

        # convert mesages into an easier format to test
        messages = [ str(msg) for msg in response.context['messages'] ]
        # last message is the publication one (preview load message still in message queue)
        self.assert_("Successfully updated" in messages[-1],
            "publication success message set in response context")        
        self.assert_('href="%s"' % reverse('fa:view-fa', kwargs={'id': 'hartsfield558'}) in messages[-1],
            'success message links to published document')
        self.assert_('William Berry Hartsfield papers' in messages[-1],
            'success message includes unit title of published document')

        # confirm that document was moved to main collection
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        self.assertEqual(docinfo['name'], settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        # confirm that document is no longer in preview collection
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)
        self.assertEqual({}, docinfo)

        task = TaskResult.objects.get(eadid='hartsfield558')
        self.assert_(isinstance(task, TaskResult),
            "TaskResult was created in db for pdf reload after successful publish from preview")

        # attempt to publish a document NOT loaded to preview
        response =  self.client.post(publish_url, {'preview_id': 'bogus345'}, follow=True)
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assert_('Publish failed. Could not retrieve' in messages[0],
            'error message set in response context attempting to publish a document not in preview')

        # force an exist save error by setting collection to a non-existent collection
        real_collection = settings.EXISTDB_ROOT_COLLECTION
        settings.EXISTDB_ROOT_COLLECTION = "/bogus/doesntexist"
        response = self.client.post(publish_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not publish",
                msg_prefix="exist save error on publish displays error to user")
        self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_ROOT_COLLECTION,
                msg_prefix="specific exist save error displayed to user")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

        # restore settings
        settings.EXISTDB_ROOT_COLLECTION = real_collection


### unit tests for findingaids.fa_admin.utils

class UtilsTest(TestCase):
    db = ExistDB()

    def tearDown(self):
        # ensure test file gets removed even if tests fail
        try:
            self.db.removeDocument(settings.EXISTDB_TEST_COLLECTION + '/hartsfield_other.xml')
        except ExistDBException, e:
            # not an error if this fails - not used by every test
            pass

    def test_check_ead(self):
        # check valid EAD - no errors  -- good fixture, should pass all tests
        dbpath = settings.EXISTDB_TEST_COLLECTION + '/hartsfield558.xml'
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

    def test_check_eadxml(self):
        eadfile = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558_invalid.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead.eadid = 'foo#~@/'    # set invalid eadid for this test only

        # invalid fixture has several errors
        errors = check_eadxml(ead)
        self.assertNotEqual(0, len(errors))
        # - series/subseries ids missing, index id missing
        self.assert_("series c01 id attribute is not set for Series 1: Personal papers, 1918-1986"
                    in errors, 'c01 missing id error reported')
        self.assert_("subseries c02 id attribute is not set for Subseries 6.1: Minerals and mining files, 1929-1970"
                    in errors, 'c02 missing id error reported')
        self.assert_("index id attribute is not set for Index of Selected Correspondents"
                    in errors, 'index missing id error reported')
        # - origination count error
        self.assert_("Site expects only one archdesc/did/origination; found 2" in errors,
                    'multiple origination error reported')
        # - whitespace in list title
        self.assert_("Found leading whitespace in list title field (origination/persname): " +
                    "'  Hartsfield, William Berry.'" in errors, 'leading whitespace in origination reported')
        # - eadid regex
        self.assert_("eadid '%s' does not match site URL regular expression" % ead.eadid
                    in errors, 'eadid regex error reported')

        # - list title first letter regex
        # simulate non-whitespace, non-alpha first letter in list title
        ead.list_title.node.text = "1234" # list title is not normally settable; overriding for test
        errors = check_eadxml(ead)
        self.assert_("First letter ('1') of list title field origination/persname does not match browse letter URL regex '%s'" \
                     % TITLE_LETTERS in errors, 'title first letter regex error reported')

        # - whitespace in control access terms
        self.assert_("Found leading whitespace in controlaccess term ' Gone with the wind (Motion picture)' (title)"
                    in errors, 'controlaccess title leading whitespace reported')
        self.assert_("Found leading whitespace in controlaccess term '  \t   Selznick, David O., 1902-1965.' (persname)" 
                    in errors, 'controlaccess name leading whitespace reported')
        self.assert_("Found leading whitespace in controlaccess term '  \t   Mines and mineral resources--Georgia.' (subject)"
                    in errors, 'controlaccess subject leading whitespace reported')
        self.assert_("Found leading whitespace in controlaccess term ' Motion pictures.' (genreform)"
                    in errors, 'controlaccess genre leading whitespace reported')        

        
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

        # whitespace cleanup
        eadfile = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558_invalid.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead = clean_ead(ead, eadfile)
        self.assertEqual(u'Hartsfield, William Berry.', unicode(ead.archdesc.origination))

        self.assertEqual(u'William Berry Hartsfield papers, circa 1860s-1983', unicode(ead.unittitle))
        self.assertEqual(u'Gone with the wind (Motion picture)',
                        ead.archdesc.controlaccess.controlaccess[0].title[0].value)
        self.assertEqual(u'Allen, Ivan.',
                        ead.archdesc.controlaccess.controlaccess[1].person_name[0].value)
        self.assertEqual(u'Mines and mineral resources--Georgia.',
                        ead.archdesc.controlaccess.controlaccess[3].subject[1].value)
        self.assertEqual(u'Motion pictures.',
                        ead.archdesc.controlaccess.controlaccess[-1].genre_form[0].value)



### unit tests for findingaids.fa_admin.tasks


# mock http objects that mimic httplib to the extent it is used in reload_cached_pdf
# used to avoid making any real http calls, allow for inspection, setting error codes, etc.

class MockHttpResponse():
    status = 200

class MockHttpConnection():
    response = MockHttpResponse()
    def request(self, method, url):
        self.method = method
        self.url = url
    def getresponse(self):
        return self.response        

class MockHttplib:
    connection = MockHttpConnection()
    def HTTPConnection(self, url):
        self.url = url
        return self.connection

def _celerytest_setUp(testcase):
    # ensure required settings are available for testing
    if hasattr(settings, 'PROXY_HOST'):
        testcase.proxy_host = settings.PROXY_HOST
        setattr(settings, 'PROXY_HOST', 'myproxy:10101')
    if hasattr(settings, 'SITE_BASE_URL'):
        testcase.site_base_url = settings.SITE_BASE_URL
        setattr(settings, 'SITE_BASE_URL', 'http://findingaids.test.edu')

    # OK, this is a little weird: swap out the real httplib in tasks with
    # the mock httplib object defined above
    testcase.real_httplib = tasks.httplib
    testcase.mock_httplib = MockHttplib()
    tasks.httplib = testcase.mock_httplib

def _celerytest_tearDown(testcase):
        if testcase.proxy_host:
            settings.PROXY_HOST = testcase.proxy_host
        if testcase.site_base_url:
            settings.SITE_BASE_URL = testcase.site_base_url


class ReloadCachedPdfTestCase(TestCase):

    def setUp(self):
        _celerytest_setUp(self)

    def tearDown(self):
        _celerytest_tearDown(self)

    def test_success(self):
        # set mock response to return 200
        self.mock_httplib.connection.response.status = 200
        result = tasks.reload_cached_pdf.delay('eadid')
        result.task_id = 'random_id'
        self.assertEquals(True, result.get(),
            "for http status 200, task result returns True")
        self.assertTrue(result.successful(),
            "for http status 200, task result successful() returns True")

        # inspect mock http objects to confirm correct urls were used
        self.assertEqual(settings.PROXY_HOST, self.mock_httplib.url,
            "http connection should use PROXY_HOST from settings; expected %s, got %s" \
            % (settings.PROXY_HOST, self.mock_httplib.url))
        self.assert_(self.mock_httplib.connection.url.startswith(settings.SITE_BASE_URL),
            "http request url should begin with SITE_BASE_URL from settings; expected starting with %s, got %s" \
            % (settings.SITE_BASE_URL, self.mock_httplib.connection.url))
        pdf_url = reverse('fa:printable-fa', kwargs={'id': 'eadid'})
        self.assert_(self.mock_httplib.connection.url.endswith(pdf_url),
            "http request url should end with PDF url; expected ending with %s, got %s" \
            % (pdf_url, self.mock_httplib.connection.url))

    def test_404(self):
        # set the response to mock returning a 404 error
        self.mock_httplib.connection.response.status = 404
        result = tasks.reload_cached_pdf.delay('eadid')
        self.assertRaises(Exception, result.get,
            "for http status 404, task result raises an Exception")
        self.assertFalse(result.successful(),
            "for http status 404, task result successful() is not True")

    def test_missing_settings(self):
        delattr(settings, 'PROXY_HOST')
        delattr(settings, 'SITE_BASE_URL')
        
        result = tasks.reload_cached_pdf.delay('eadid')
        self.assertRaises(Exception, result.get,
            "when required settings are missing, task raises an Exception")
        
