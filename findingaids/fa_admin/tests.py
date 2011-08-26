import cStringIO
import logging
from mock import patch
import os
import re
from shutil import rmtree, copyfile
import sys
import tempfile
from time import sleep

from django.test import Client, TestCase
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.http import HttpRequest

from eulcore.django.existdb.db import ExistDB, ExistDBException
from eulcore.django.taskresult.models import TaskResult
from eulcore.django.test import TestCase
from eulcore.xmlmap.core import load_xmlobject_from_file
from eulcore.xmlmap.eadmap import EAD_NAMESPACE


from findingaids.fa.models import FindingAid, Deleted
from findingaids.fa.urls import TITLE_LETTERS
from findingaids.fa_admin import tasks, views, utils
from findingaids.fa_admin.views import _get_recent_xml_files
from findingaids.fa_admin.management.commands import prep_ead as prep_ead_cmd
from findingaids.fa_admin.management.commands import unitid_identifier 
from findingaids.fa_admin.mocks import MockDjangoPidmanClient, MockHttplib

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
        self.real_exist_url = settings.EXISTDB_SERVER_URL
        self._existdb_user = getattr(settings, 'EXISTDB_SERVER_USER', None)
        self._existdb_password = getattr(settings, 'EXISTDB_SERVER_PASSWORD', None)

        # save pid config settings to restore in teardown
        self._pid_config = {
            'PIDMAN_HOST': settings.PIDMAN_HOST,
            'PIDMAN_USER': settings.PIDMAN_USER,
            'PIDMAN_PASSWORD': settings.PIDMAN_PASSWORD,
            'PIDMAN_DOMAIN' : settings.PIDMAN_DOMAIN
            }
        self._django_pid_client = views.utils.DjangoPidmanRestClient
        views.utils.DjangoPidmanRestClient = MockDjangoPidmanClient

    def tearDown(self):
        if hasattr(self, '_stored_ead_src'):
            settings.FINDINGAID_EAD_SOURCE = self._stored_ead_src

        # clean up temp files & dir
        rmtree(self.tmpdir)

        # restore existdb settings
        settings.EXISTDB_ROOT_COLLECTION = self.real_collection
        settings.EXISTDB_PREVIEW_COLLECTION = self.preview_collection
        settings.EXISTDB_SERVER_URL = self.real_exist_url
        settings.EXISTDB_SERVER_USER = self._existdb_user
        settings.EXISTDB_SERVER_PASSWORD = self._existdb_password

        # restore pid config settings
        for key, val in self._pid_config.iteritems():
            setattr(settings, key, val)

        MockDjangoPidmanClient.search_result = MockDjangoPidmanClient.search_result_nomatches
        views.utils.DjangoPidmanRestClient = self._django_pid_client

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
        # TEMPORARY: suppressing publish on list documents to assess workflow
        #publish_url = reverse('fa-admin:publish-ead')
        #self.assertContains(response, '<form action="%s" method="post"' % publish_url)
        #self.assertContains(response, '<button type="submit" name="filename" value="%s" '
        #        % os.path.basename(self.tmpfiles[0].name))
        # file list contains buttons to preview documents
        preview_url = reverse('fa-admin:preview-ead')
        self.assertContains(response, '<form action="%s" method="post"' % preview_url)
        self.assertContains(response, '<button type="submit" name="filename" value="%s" '
                % os.path.basename(self.tmpfiles[0].name), 1)
        # file list contains link to prep documents
        prep_url = reverse('fa-admin:prep-ead-about', args=[os.path.basename(self.tmpfiles[0].name)])
        self.assertContains(response, 'href="%s">PREP</a>' % prep_url)
        # contains pagination
        self.assertPattern('Pages:\s*1', response.content)

        # TODO: test last published date / preview load date?
        # This will require eXist fixtures that match the temp files

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
        preview_docurl = reverse('fa-admin:preview:findingaid', kwargs={'id': eadid})
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
        self.assertContains(response, reverse('fa-admin:preview:findingaid', kwargs={'id': 'hartsfield558'}),
            msg_prefix="preview summary should link to preview page for document loaded to preview")
        self.assertContains(response, 'last modified: 0 minutes ago',
            msg_prefix="preview summary listing includes modification time")
            
        # preview page should include publish form for users with permission to publish
        preview_fa_url = reverse('fa-admin:preview:findingaid', kwargs={'id': eadid})
        response = self.client.get(preview_fa_url)
        self.assertContains(response,
                '<form id="preview-publish" action="%s" method="post"' % reverse('fa-admin:publish-ead'),
                msg_prefix="preview page includes publish form")
        publish_submit = 'type="submit" name="preview_id" value="%s">PUBLISH' % eadid
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
        self.assertContains(response, """The attribute &#39;invalid&#39; is not allowed""")   # schema validation error
        self.assertContains(response, "Additional Instructions",
                msg_prefix="error page displays instructions & next steps to user")

        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/hartsfield558_invalid.xml')
        self.assertEqual({}, docinfo, "invalid xml document not loaded to exist preview")


        # exist save errors should be caught & handled gracefully
        # - force an error by setting preview collection to a non-existent collection
        settings.EXISTDB_PREVIEW_COLLECTION = "/bogus/doesntexist"
        response = self.client.post(preview_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not preview")
        self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_PREVIEW_COLLECTION)     
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

        # simulate incorrect eXist permissions by not specifying username/password
        settings.EXISTDB_PREVIEW_COLLECTION = self.preview_collection   # restore setting
        # ensure guest account cannot update
        self.db.setPermissions(settings.EXISTDB_PREVIEW_COLLECTION, 'other=-update')

        settings.EXISTDB_SERVER_USER = None
        settings.EXISTDB_SERVER_PASSWORD = None
        
        response = self.client.post(preview_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not preview")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")
        self.assertContains(response, "not allowed to write to collection",
                msg_prefix="error page displays specific eXist permission message")

        # - simulate eXist not running by setting existdb url to non-existent exist
        settings.EXISTDB_SERVER_URL = 'http://kamina.library.emory.edu:9191/not-exist'
        response = self.client.post(preview_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not preview")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")
        self.assertContains(response, "I/O Error: Connection refused",
                msg_prefix="error page displays specific connection error message")

        
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
        
    def test_prep_ead(self):
         # use fixture directory to test publication
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')

        prep_xml = reverse('fa-admin:prep-ead', args=[filename])
        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        prep_diff = reverse('fa-admin:prep-ead-diff', args=[filename])
        
        self.client.login(**self.credentials['admin'])
        response = self.client.get(prep_summary)

        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_summary))
        self.assert_(response.context['changes'])
                        
        self.assertContains(response, 'Prepared EAD for %s' % filename)
        self.assertContains(response, 'View file differences line by line')
        self.assertContains(response, prep_diff,
                            msg_prefix="Prepared EAD summary should link to line-by-line diff")
        self.assertPattern('<p class="removed".*>-.*c01.*id=.*s1', response.content)
        self.assertPattern('<p class="added".*>+.*c01.*id=.*hartsfield558_series1.*', response.content)
        self.assertContains(response, prep_xml,
                            msg_prefix="prepared EAD summary should link to xml download")

        response = self.client.get(prep_diff)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_diff))
        # output is generated by difflib; just testing that response has content
        self.assertContains(response, '<table')

        response = self.client.get(prep_xml)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, prep_xml))
        expected = 'application/xml'
        self.assertEqual(response['Content-Type'], expected, "Expected '%s' but returned '%s' for %s mimetype" % \
                        (expected, response['Content-Type'], prep_xml))
        self.assertEqual(response['Content-Disposition'], "attachment; filename=%s" % filename)
        self.assertContains(response, "xsi:schemaLocation",
                    msg_prefix="response does not lose XSD schema location from original xml")
        self.assertContains(response, "encoding='UTF-8'",
                    msg_prefix="response includes charater encoding declaration")
        self.assertContains(response, "encoding='UTF-8'",
                    msg_prefix="response includes charater encoding declaration")
        self.assertContains(response, 'hartsfield558</eadid>')
        self.assertContains(response, '<c01 level="series" id="hartsfield558_series1"')
        self.assertContains(response, '<c02 level="subseries" id="hartsfield558_subseries6.1"')
        self.assertContains(response, '<index id="hartsfield558_index1">')

        # prep an ead that doesn't need any changes
        filename = 'abbey244.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa', 'fixtures')

        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        response = self.client.get(prep_summary, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (following redirects, prep EAD)'
                             % (expected, code, prep_summary))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (prepared EAD)'
                             % (expected, code, prep_summary))
        messages = [ str(msg) for msg in response.context['messages'] ]
        self.assert_("No changes made to <b>%s</b>" % filename in messages[0])
        self.assert_("already prepared" in messages[0])

        # prep an ead that needs an ARK, force ark generation error
        MockDjangoPidmanClient.raise_error = (401, 'unauthorized')
        filename = 'bailey807.xml'
        prep_xml = reverse('fa-admin:prep-ead', args=[filename])
        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        response = self.client.get(prep_summary, follow=True)
        # summary should be 200, display prep error
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected,
            'Expected %s but returned %s for %s (following redirects, prep EAD)' \
             % (expected, code, prep_summary))
        self.assertContains(response, 'Failed to prep the document')
        self.assertContains(response, 'There was an error preparing the file')

        MockDjangoPidmanClient.raise_error = (401, 'unauthorized')
        response = self.client.get(prep_xml)
        expected = 500
        self.assertEqual(response.status_code, expected,
            'Expected %s but returned %s for %s (prep ead, ARK generation error)' % \
            (expected, response.status_code, prep_xml))


    def test_prep_ark_messages(self):
        # test that ARK generation messages are displayed to user
        # NOTE: calling the view directly so the pid client result can be mocked
        _real_pid_client = views.utils.DjangoPidmanRestClient
        views.utils.DjangoPidmanRestClient = MockDjangoPidmanClient
        MockDjangoPidmanClient.search_result = {
            'results_count': 2,
            'results': [
                {
                    'pid': '123',
                    'targets': [{'access_uri': 'http://so.me/ark:/123/45b'}, ]
                },
            ]
        }
        # use django test client to login and setup session
        self.client.login(**self.credentials['admin'])
        request = HttpRequest()
        request.user = User.objects.get(username=self.credentials['admin']['username'])
        request.session = self.client.session

        # use a fixture that does not have an ARK
        filename = 'bailey807.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa', 'fixtures')
        response = views.prepared_eadxml(request, filename)
        # retrieve messages from the request
        msgs = messages.get_messages(request)
        self.assert_('Found 2 ARKs when searching' in msgs[0],
            'multiple ARK warning is set in messages')
        self.assert_('Using existing ARK' in msgs[1],
            'using existing ARK info is set in messages ')

        # restore non-mock pid client
        views.utils.DjangoPidmanRestClient = _real_pid_client
        
    def test_prep_badlyformedxml(self):
        # use fixture directory to test publication
        filename = 'badlyformed.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')

        prep_xml = reverse('fa-admin:prep-ead', args=[filename])
        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        prep_diff = reverse('fa-admin:prep-ead-diff', args=[filename])

        self.client.login(**self.credentials['admin'])
        response = self.client.get(prep_xml)
        expected = 500
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s (non-well-formed xml)' % \
                        (expected, response.status_code, prep_summary))

        response = self.client.get(prep_summary)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_summary))

        self.assertContains(response, 'Could not load document',
                msg_prefix='error loading document displayed')
        self.assertContains(response, 'not allowed in attributes',
                msg_prefix='xml syntax error displayed')
        self.assertNotContains(response, prep_diff,
                msg_prefix="prep summary for badly formed xml should NOT link to line-by-line diff")
        self.assertNotContains(response, prep_xml,
                msg_prefix="prep summary for badly formed xml should NOT link to xml for download")
        

    # tests for view helper functions

    def test_get_recent_xml_files(self):
        recent_xml = _get_recent_xml_files(self.tmpdir)
        self.assertEqual(3, len(recent_xml))
        # should be in reverse order - last created first
        self.assertEqual(recent_xml[0].filename, os.path.basename(self.tmpfiles[2].name))
        self.assertEqual(recent_xml[1].filename, os.path.basename(self.tmpfiles[1].name))
        self.assertEqual(recent_xml[2].filename, os.path.basename(self.tmpfiles[0].name))
        # non-xml file not included
        filenames = [eadfile.filename for eadfile in recent_xml]
        self.assert_(os.path.basename(self.nonxml_tmpfile.name) not in filenames)


    def test_list_published(self):
        # login to test admin-only view
        self.client.login(**self.credentials['admin'])

        list_published_url = reverse('fa-admin:list-published')
        response = self.client.get(list_published_url)
        self.assertContains(response, "Published Finding Aids")

        fa = response.context['findingaids']
        self.assert_(fa,"findingaids is set in response context")
        self.assertEqual(fa.object_list[0].eadid.value, 'hartsfield558',
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

        task = TaskResult.objects.get(object_id='hartsfield558')
        self.assert_(isinstance(task, TaskResult), 
            "TaskResult was created in db for pdf reload after successful publish")

        # publish invalid document - should display errors
        response = self.client.post(publish_url, {'filename' : 'hartsfield558_invalid.xml'})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, invalid document) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, "Could not publish")
        self.assertContains(response, "The attribute &#39;invalid&#39; is not allowed")   # DTD validation error
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

        # exist save errors should be caught & handled gracefully
        # - force an exist save error by setting collection to a non-existent collection
        settings.EXISTDB_ROOT_COLLECTION = "/bogus/doesntexist"
        response = self.client.post(publish_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not publish",
                msg_prefix="exist save error on publish displays error to user")
        self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_ROOT_COLLECTION,
                msg_prefix="specific exist save error displayed to user")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

        # simulate incorrect eXist permissions by not specifying username/password
        settings.EXISTDB_ROOT_COLLECTION = self.real_collection # restore
        # ensure guest account cannot update
        self.db.setPermissions(settings.EXISTDB_ROOT_COLLECTION, 'other=-update')

        settings.EXISTDB_SERVER_USER = None
        settings.EXISTDB_SERVER_PASSWORD = None

        response = self.client.post(publish_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not publish")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")
        self.assertContains(response, "update is not allowed",
                msg_prefix="error page displays specific exist permissions message")

        # - simulate eXist not running by setting existdb url to non-existent exist
        settings.EXISTDB_SERVER_URL = 'http://kamina.library.emory.edu:9191/not-exist'
        response = self.client.post(publish_url, {'filename' : 'hartsfield558.xml'})
        self.assertContains(response, "Could not publish")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")
        self.assertContains(response, "I/O Error: Connection refused",
                msg_prefix="error page displays specific connection error message")


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
        self.assert_('href="%s"' % reverse('fa:findingaid', kwargs={'id': 'hartsfield558'}) in messages[-1],
            'success message links to published document')
        self.assert_('William Berry Hartsfield papers' in messages[-1],
            'success message includes unit title of published document')

        # confirm that document was moved to main collection
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        self.assertEqual(docinfo['name'], settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        # confirm that document is no longer in preview collection
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)
        self.assertEqual({}, docinfo)

        task = TaskResult.objects.get(object_id='hartsfield558')
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

    def setUp(self):
        # temporarily replace pid client with mock for testing
        self._django_pid_client = utils.DjangoPidmanRestClient
        utils.DjangoPidmanRestClient = MockDjangoPidmanClient

        # save pid config settings to restore in teardown
        self._pid_config = {
            'PIDMAN_HOST': settings.PIDMAN_HOST,
            'PIDMAN_USER': settings.PIDMAN_USER,
            'PIDMAN_PASSWORD': settings.PIDMAN_PASSWORD,
            'PIDMAN_DOMAIN' : settings.PIDMAN_DOMAIN
            }

        # initialize valid and invalid ead fixtures
        self.valid_eadfile = os.path.join(settings.BASE_DIR, 'fa_admin',
            'fixtures', 'hartsfield558.xml')
        self.valid_ead = load_xmlobject_from_file(self.valid_eadfile, FindingAid)

        self.invalid_eadfile = os.path.join(settings.BASE_DIR, 'fa_admin',
            'fixtures', 'hartsfield558_invalid.xml')
        self.invalid_ead = load_xmlobject_from_file(self.invalid_eadfile, FindingAid)

    def tearDown(self):
        # ensure test file gets removed even if tests fail
        try:
            self.db.removeDocument(settings.EXISTDB_TEST_COLLECTION + '/hartsfield_other.xml')
        except ExistDBException, e:
            # not an error if this fails - not used by every test
            pass

        MockDjangoPidmanClient.search_result = MockDjangoPidmanClient.search_result_nomatches
        # restore non-mock client
        utils.DjangoPidmanRestClient = self._django_pid_client
        # restore pid config settings
        for key, val in self._pid_config.iteritems():
            setattr(settings, key, val)

    def test_check_ead(self):
        # check valid EAD - no errors  -- good fixture, should pass all tests
        dbpath = settings.EXISTDB_TEST_COLLECTION + '/hartsfield558.xml'
        errors = utils.check_ead(self.valid_eadfile, dbpath)
        self.assertEqual(0, len(errors))

        # should cause several errors - not schema valid, eadid, series/subseries ids missing, index id missing
        errors = utils.check_ead(self.invalid_eadfile, dbpath)
        self.assertNotEqual(0, len(errors))
        self.assert_("attribute 'invalid': The attribute 'invalid' is not allowed"
                     in errors[0])   # validation error message
        self.assert_("Line 2" in errors[0], "validation error includes line number")   # validation error message
        self.assert_("eadid 'hartsfield558.xml' does not match expected value" in errors[1])
        self.assert_("series c01 id attribute is not set for Series 1" in errors[2])
        self.assert_("subseries c02 id attribute is not set for Subseries 6.1" in errors[3])
        self.assert_("index id attribute is not set for Index of Selected Correspondents" in errors[4])

        # eadid uniqueness check in eXist
        self.db.load(open(self.valid_eadfile), dbpath, True)
        errors = utils.check_ead(self.valid_eadfile, dbpath)
        # same eadid, but present in the file that will be updated - no errors
        self.assertEqual(0, len(errors))

        # upload same file to a different path - non-unique eadid error
        self.db.load(open(self.valid_eadfile), settings.EXISTDB_TEST_COLLECTION + '/hartsfield_other.xml', True)
        errors = utils.check_ead(self.valid_eadfile, dbpath)
        self.assertEqual(1, len(errors))
        self.assert_("Database already contains 2 instances of eadid" in errors[0])

        # remove version with correct path to test single conflicting eadid
        self.db.removeDocument(dbpath)
        errors = utils.check_ead(self.valid_eadfile, dbpath)
        self.assertEqual(1, len(errors))
        self.assert_("Database contains eadid 'hartsfield558' in a different document" in errors[0])

    def test_check_eadxml(self):
        # use invalid ead fixture to check error detection
        ead = self.invalid_ead
        ead.eadid.value = 'foo#~@/'    # set invalid eadid for this test only

        # invalid fixture has several errors
        errors = utils.check_eadxml(ead)
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
        self.assert_("eadid '%s' does not match site URL regular expression" % ead.eadid.value
                    in errors, 'eadid regex error reported')

        #ARK in url and identifier not set or invalid
        self.assert_("eadid url is either not set or not an ARK. " +
            "To correct, run the prep process again."
                    in errors, 'eadid ark not in url')
        self.assert_("eadid identifier is either not set or not an ARK" +
            "To correct, run the prep process again."
                    in errors, 'eadid ark not in identifier')

        #valid ARKs in url and identifier but do not match
        ark1 = "http://testpid.library.emory.edu/ark:/25593/1234"
        ark1_short = "ark:/25593/1234"
        ark2_short = "ark:/25593/567"
        ead.eadid.url = ark1
        ead.eadid.identifier =  ark2_short
        errors = utils.check_eadxml(ead)
        
        self.assert_("eadid url is either not set or not an ARK. " +
            "To correct, run the prep process again."
                    not in errors, 'valid eadid ark set in url')
        self.assert_("eadid identifier is either not set or not an ARK" +
            "To correct, run the prep process again."
                    not in errors, 'valid eadid ark set in identifier')

        self.assert_("eadid url and identifier do not match: url '%s' should end with identifier '%s'" % (ark1, ark2_short)
                    in errors, 'eadid url and  identifier do not march')

        #Change url  and identifier to match
        ead.eadid.url = ark1
        ead.eadid.identifier =  ark1_short
        errors = utils.check_eadxml(ead)

        self.assert_("eadid url and identifier do not match: url '%s' should end with identifier '%s'" % (ark1, ark1_short)
                    not in errors, 'eadid url and  identifier march')

        # - list title first letter regex
        # simulate non-whitespace, non-alpha first letter in list title
        ead.list_title.node.text = "1234" # list title is not normally settable; overriding for test
        errors = utils.check_eadxml(ead)
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

        # - did with > 2 containers
        self.assert_('Site expects maximum of 2 containers per did; found 1 did(s) with more than 2'
                    in errors, 'did with more than 2 containers reported')

        # - did with only 1 container
        self.assert_('Site expects 2 containers per did; found 1 did(s) with only 1'
                    in errors, 'did with only 1 container reported')

        # make sure we handle quirky document with a <title> at the beginning of the <unittitle> 
        eadfile = os.path.join(settings.BASE_DIR, 'fa',
            'fixtures', 'pittsfreeman1036.xml')
        ead_nested_title = load_xmlobject_from_file(eadfile, FindingAid)
        errors = utils.check_eadxml(ead_nested_title)
        self.assert_(all('list title' not in err for err in errors),
                     'nested <title> in <unittitle> should not generate a list title whitespace error')

        
    def test_prep_ead(self):
        # valid fixtures is an ead with series/subseries, and index
        # - clear out fixture ark url to trigger generating a new one (simulated)
        del(self.valid_ead.eadid.url)
        del(self.valid_ead.eadid.identifier)
        ead = utils.prep_ead(self.valid_ead, self.valid_eadfile)
        self.assert_(isinstance(ead, FindingAid), "prep_ead should return an instance of FindingAid")
        self.assertEqual(u'hartsfield558', ead.eadid.value)
        self.assertEqual(u'hartsfield558_series1', ead.dsc.c[0].id)
        self.assertEqual(u'hartsfield558_subseries6.1', ead.dsc.c[5].c[0].id)
        self.assertEqual(u'hartsfield558_index1', ead.archdesc.index[0].id)
        # ark should be generated and stored in eadid url
        self.assertEqual(MockDjangoPidmanClient.test_ark, ead.eadid.url)
        # short-form ark should be stored in identifier attribute
        self.assert_(MockDjangoPidmanClient.test_ark.endswith(ead.eadid.identifier))

        # ead with no series
        eadfile = os.path.join(settings.BASE_DIR, 'fa', 'fixtures', 'pittsfreeman1036.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead = utils.prep_ead(ead, eadfile)
        self.assert_(isinstance(ead, FindingAid), "prep_ead should return an instance of FindingAid")
        self.assertEqual(u'pittsfreeman1036', ead.eadid.value)

        # series with no unitid
        eadfile = os.path.join(settings.BASE_DIR, 'fa', 'fixtures', 'raoul548.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead = utils.prep_ead(ead, eadfile)
        self.assertEqual(u'raoul548_series3', ead.dsc.c[2].id)

        # whitespace cleanup
        ead = utils.prep_ead(self.invalid_ead, self.invalid_eadfile)
        # - no leading whitespace in list title
        # ead.archdesc.origination is getting normalized, so can't be used for testing
        origination = ead.node.xpath('//e:origination/e:persname', namespaces={'e': EAD_NAMESPACE})
        self.assertEqual(u'Hartsfield, William Berry.', origination[0].text)
        # test the node text directly (does not include unitdate)
        self.assertEqual(u'William Berry Hartsfield papers, ', ead.unittitle.node.text)        
        self.assertEqual(u'Gone with the wind (Motion picture)',
                        ead.archdesc.controlaccess.controlaccess[0].title[0].value)
        self.assertEqual(u'Allen, Ivan.',
                        ead.archdesc.controlaccess.controlaccess[1].person_name[0].value)
        self.assertEqual(u'Mines and mineral resources--Georgia.',
                        ead.archdesc.controlaccess.controlaccess[3].subject[1].value)
        # unicode characters
        self.assertEqual(u'Motion pictures--Georgia. \u2026',
                        ead.archdesc.controlaccess.controlaccess[3].subject[2].value)
        self.assertEqual(u'Motion pictures.',
                        ead.archdesc.controlaccess.controlaccess[-1].genre_form[0].value)
        # remaining errors after clean-up:
        # 1 - duplicate origination
        # 2 - > 2 containers in a did (summary error and list of problem dids)
        # 2 - 1 container in a did (summary error and list of problem dids)
        # = 5
        self.assertEqual(5, len(utils.check_eadxml(ead)),
            "only 3 errors (duplicate origination, 3 containers in a did, 1 container in a did) should be left in invalid test fixture after cleaning")

        # special case - unittitle begins with a <title>
        eadfile = os.path.join(settings.BASE_DIR, 'fa', 'fixtures', 'pittsfreeman1036.xml')
        ead = load_xmlobject_from_file(eadfile, FindingAid)
        ead = utils.prep_ead(ead, eadfile)
        self.assertFalse(unicode(ead.list_title).startswith('None'),
            'cleaned unittitle with leading <title> should not start with "None"')

    def test_generate_ark(self):
        # successful case
        utils.generate_ark(self.valid_ead)
        self.assertEqual(MockDjangoPidmanClient.url,
                        settings.SITE_BASE_URL.rstrip('/') + '/documents/hartsfield558/',
                        'pid target URI is site url for ead document')
        self.assertEqual(MockDjangoPidmanClient.name, unicode(self.valid_ead.unittitle),
                        'pid name is ead document unittitle')
        self.assertEqual(settings.PIDMAN_DOMAIN, MockDjangoPidmanClient.domain,
                        'create pid used configured site pid domain')

    def test_generate_ark_badconfig(self):
        # missing config settings required for initializing pidman client
        del(settings.PIDMAN_HOST)
        # capture the exception to do minimal inspecting
        try:
            utils.generate_ark(self.valid_ead)
        except Exception as e:
            ex = e

        self.assert_('Error initializing' in str(ex))

    def test_generate_ark_nodomain(self):
        # missing config settings for pid domain
        del(settings.PIDMAN_DOMAIN)
        # capture the exception to inspect it
        try:
            utils.generate_ark(self.valid_ead)
        except Exception as e:
            ex = e

        self.assert_('PID manager domain is not configured' in str(ex))

    def test_generate_ark_serviceerror(self):
        MockDjangoPidmanClient.raise_error = (401, 'unauthorized')
        # handle errors that could come back from the server
        try:
            utils.generate_ark(self.valid_ead)
        except Exception as e:
            ex = e
        self.assert_(isinstance(ex, Exception),
            "an exception should be raised when PID client gets a 401 response")
        self.assert_('Error generating ARK' in str(ex),
            'exception text indicates the error was while attempting to generate an ARK')
        self.assert_('unauthorized' in str(ex),
            'exception text includes error detail from pidmanclient exception')

    def test_generate_ark_existing_pid(self):
        # simulate search finding one ark before new ark is generated
        found_ark = 'http://pid.emory.edu/ark:/78912/16x3n'
        # create mock search result with one match
        MockDjangoPidmanClient.search_result = {
            'results_count': 1,
            'results': [
                {
                    'pid': '16x3n',
                    'targets': [{'access_uri': found_ark}, ]
                },
            ]
        }

        # capture logging output in a stream
        buffer = cStringIO.StringIO()
        logger = logging.getLogger()
        sh = logging.StreamHandler(buffer)
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        
        ark = utils.generate_ark(self.valid_ead)

        logger.removeHandler(sh)
        log_output = buffer.getvalue()
        
        self.assertEqual(found_ark, ark,
            'generate ark returns access uri from search results')
        search_args = MockDjangoPidmanClient.search_args
        self.assertEqual(settings.PIDMAN_DOMAIN, search_args['domain_uri'],
            'pid search uses configured PID domain')
        self.assertEqual('ark', search_args['type'],
            'pid search is restricted to type=ark')
        self.assert_(search_args['target'].endswith('/documents/hartsfield558/'))
        self.assert_('Using existing ARK' in log_output,
            'log reports an existing ARK was used')

    def test_generate_ark_existing_pids(self):
        # simulate search finding multiple pids 
        found_ark = 'http://pid.emory.edu/ark:/78912/16x3n'
        # create mock search result with two matches
        MockDjangoPidmanClient.search_result = {
            'results_count': 2,
            'results': [
                {
                    'pid': '16x3n',
                    'targets': [{'access_uri': found_ark}, ]
                },
            ]
        }
        # capture logging output in a stream
        buffer = cStringIO.StringIO()
        logger = logging.getLogger()
        sh = logging.StreamHandler(buffer)
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)

        ark = utils.generate_ark(self.valid_ead)

        logger.removeHandler(sh)
        log_output = buffer.getvalue()

        self.assertEqual(found_ark, ark,
            'generate ark returns access uri from search results')
        self.assert_('Found 2 ARKs' in log_output,
            'log reports that multiple ARKs were found')


### unit tests for findingaids.fa_admin.tasks

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
    # testcase.real_httplib = tasks.httplib
    # testcase.mock_httplib = MockHttplib()
    # tasks.httplib = testcase.mock_httplib

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

    @patch('findingaids.fa_admin.tasks.urllib2')
    def test_success(self, mockurllib2):
        # set mock response to return 200
        mockurllib2.urlopen.return_value.code = 200
        #request = urllib2.Request(url, None, refresh_cache)
        #response = urllib2.urlopen(request)
        #logger.debug('Response headers: \n%s' % response.info())
        result = tasks.reload_cached_pdf.delay('eadid')
        result.task_id = 'random_id'
        self.assertEquals(True, result.get(),
            "for http status 200, task result returns True")
        self.assertTrue(result.successful(),
            "for http status 200, task result successful() returns True")

        # inspect mock urllib2 objects to confirm correct urls were used
        #proxy_args, proxy_kwargs = mockurllib2.ProxyHandler.call_args
        mockurllib2.ProxyHandler.assert_called_with({'http': settings.PROXY_HOST})
#        print 'debug proxy args are ', proxy_args
        # self.assertEqual(settings.PROXY_HOST, proxy_args['http'],
        #     "http connection should use PROXY_HOST from settings; expected %s, got %s" \
        #     % (settings.PROXY_HOST, proxy_args['http']))

        rqst_args, rqst_kwargs = mockurllib2.Request.call_args
        # request args : url, data, headers
        rqst_url = rqst_args[0]
        rqst_headers = rqst_args[2]
        self.assert_(rqst_url.startswith(settings.SITE_BASE_URL),
                     "http request url should begin with SITE_BASE_URL from settings; expected starting with %s, got %s" \
                     % (settings.SITE_BASE_URL, rqst_url))
        pdf_url = reverse('fa:printable', kwargs={'id': 'eadid'})
        self.assert_(rqst_url.endswith(pdf_url),
            "http request url should end with PDF url; expected ending with %s, got %s" \
            % (pdf_url, rqst_url))
        
        self.assertEqual(rqst_headers['Cache-Control'], 'max-age=0')

    @patch('findingaids.fa_admin.tasks.urllib2')
    def test_404(self, mockurllib2):
        # set the response to mock returning a 404 error
        mockurllib2.urlopen.return_value.code = 404
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
        

### unit tests for django-admin manage commands

class TestCommand(BaseCommand):
    output = ''
    # test command class to simplify calling a command as if running from the commandline
    # base command will set up default args before calling handle method
    def run_command(self, *args):
        '''Run the command as if calling from command line by giving a list
        of command-line arguments, e.g.::

            command.run_command('-n', '-v', '2')

        :param args: list of command-line arguments
        '''
        # capture stdout & stderr for testing output results
        buffer = cStringIO.StringIO()
        sys.stdout = buffer
        sys.stderr = buffer
        try:
            # run from argv expects command, subcommand, then any arguments
            run_args = ['manage.py', 'command-name']
            run_args.extend(args)
            result = self.run_from_argv(run_args)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        self.output = buffer.getvalue()

        return result


class PrepEadTestCommand(prep_ead_cmd.Command, TestCommand):
    pass

class PrepEadCommandTest(TestCase):
    def setUp(self):
        self.command = PrepEadTestCommand()
        # store settings that may be changed/removed by tests
        self._ead_src = settings.FINDINGAID_EAD_SOURCE
        self._existdb_root = settings.EXISTDB_ROOT_COLLECTION
        self._pidman_pwd = settings.PIDMAN_PASSWORD
        
        self.tmpdir = tempfile.mkdtemp(prefix='findingaids-prep_ead-test')
        settings.FINDINGAID_EAD_SOURCE = self.tmpdir

        settings.PIDMAN_PASSWORD = 'this-better-not-be-a-real-password'

        # temporarily replace pid client with mock for testing
        self._django_pid_client = prep_ead_cmd.utils.DjangoPidmanRestClient
        prep_ead_cmd.utils.DjangoPidmanRestClient = MockDjangoPidmanClient

        self.files = {}
        self.file_sizes = {}    # store file sizes to check modification
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        for file in ['hartsfield558.xml', 'hartsfield558_invalid.xml', 'badlyformed.xml']:
            # store full path to tmp copy of file
            self.files[file] = os.path.join(self.tmpdir, file)
            copyfile(os.path.join(fixture_dir, file), self.files[file])
            self.file_sizes[file] = os.path.getsize(self.files[file])

    def tearDown(self):
        # remove any files created in temporary test staging dir
        rmtree(self.tmpdir)
        # restore real settings
        settings.FINDINGAID_EAD_SOURCE = self._ead_src
        settings.EXISTDB_ROOT_COLLECTION = self._existdb_root
        settings.PIDMAN_PASSWORD = self._pidman_pwd

        MockDjangoPidmanClient.search_result = MockDjangoPidmanClient.search_result_nomatches
        prep_ead_cmd.utils.DjangoPidmanRestClient = self._django_pid_client

    def test_missing_ead_source_setting(self):
        del(settings.FINDINGAID_EAD_SOURCE)
        self.assertRaises(CommandError, self.command.handle, verbosity=0)

    def test_missing_existdb_setting(self):
        del(settings.EXISTDB_ROOT_COLLECTION)
        self.assertRaises(CommandError, self.command.handle, verbosity=0)

    def test_prep_all(self):
        # force ark generation error
        MockDjangoPidmanClient.raise_error = (401, 'unauthorized')
        
        # with no filenames - should process all files
        self.command.run_command('-v', '2')
        output = self.command.output
        
        # badly-formed xml - should be reported
        self.assert_(re.search(r'^Error.*badlyformed.xml.*not well-formed.*$', output, re.MULTILINE),
            'prep_ead reports error for non well-formed xml')
        # invalid - should result in error on attempted ark generation
        self.assert_(re.search(r'Error: failed to prep .*hartsfield558_invalid.xml', output),
            'prep_ead reports prep/ark generation error')
        self.assert_(re.search(r'Updated .*hartsfield558.xml', output),
            'in verbose mode, prep_ead reports updated document')

        # files with errors should not be modified
        self.assertEqual(self.file_sizes['hartsfield558_invalid.xml'],
                        os.path.getsize(self.files['hartsfield558_invalid.xml']),
                    'file with errors not modified by prep_ead script when updating all documents')
        self.assertEqual(self.file_sizes['badlyformed.xml'],
                        os.path.getsize(self.files['badlyformed.xml']),
                    'file with errors not modified by prep_ead script when updating all documents')

    def test_prep_single(self):
        # copy valid file so there are two files that could be changed
        hfield_copy = os.path.join(self.tmpdir, 'hartsfield558-2.xml')
        copyfile(os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558.xml'),
                 hfield_copy)
        self.file_sizes['hartsfield558-2.xml'] = os.path.getsize(hfield_copy)
                 
       
        # process a single file
        self.command.run_command('hartsfield558.xml')
        output = self.command.output

        self.assert_('1 document updated' in output)
        self.assert_('0 documents unchanged' in output)
        self.assert_('0 documents with errors' in output)

        # using file-size as a convenient way to check which files were modified
        self.assertNotEqual(self.file_sizes['hartsfield558.xml'],
                            os.path.getsize(self.files['hartsfield558.xml']),
                            'specified file was modified by prep_ead script')
        self.assertEqual(self.file_sizes['hartsfield558-2.xml'],
                        os.path.getsize(hfield_copy),
                    'in single-file mode, non-specified file not modified by prep_ead script')

    def test_prep_ark_messages(self):
        MockDjangoPidmanClient.search_result = {
            'results_count': 2,
            'results': [
                {
                    'pid': '16x3n',
                    'targets': [{'access_uri': 'http://pid/ark:/123/34c'}, ]
                },
            ]
        }

        # run on a single file where ark generation will be attempted
        self.command.run_command('hartsfield558_invalid.xml')
        output = self.command.output

        self.assert_('WARNING: Found 2 ARKs'  in output)
        self.assert_('INFO: Using existing ARK' in output)



class UnitidIdentifierTestCommand(unitid_identifier.Command, TestCommand):
    pass

class UnitidIdentifierCommandTest(TestCase):
    def setUp(self):
        self.command = UnitidIdentifierTestCommand()
        # store settings that may be changed/removed by tests
        self._ead_src = settings.FINDINGAID_EAD_SOURCE

        self.tmpdir = tempfile.mkdtemp(prefix='findingaids-unitid_identifier-test')
        settings.FINDINGAID_EAD_SOURCE = self.tmpdir

        self.files = {}
        self.file_sizes = {}    # store file sizes to check modification
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        for file in ['hartsfield558.xml', 'hartsfield558_invalid.xml', 'badlyformed.xml']:
            # store full path to tmp copy of file
            self.files[file] = os.path.join(self.tmpdir, file)
            copyfile(os.path.join(fixture_dir, file), self.files[file])
            self.file_sizes[file] = os.path.getsize(self.files[file])

    def tearDown(self):
        # remove any files created in temporary test staging dir
        rmtree(self.tmpdir)
        # restore real settings
        settings.FINDINGAID_EAD_SOURCE = self._ead_src

    def test_run(self):
        # process all files
        self.command.run_command('-v', '2')
        output = self.command.output

        # check that correct unitid identifier was set
        ead = load_xmlobject_from_file(self.files['hartsfield558.xml'], FindingAid)
        self.assertEqual(558, ead.archdesc.unitid.identifier)
        self.assert_('2 documents updated' in output)
        self.assert_('1 document with errors' in output)

        # badly-formed xml - should be reported
        self.assert_(re.search(r'^Error.*badlyformed.xml.*not well-formed.*$', output, re.MULTILINE),
            'unitid_identifier reports error for non well-formed xml')

        # files with errors should not be modified
        self.assertEqual(self.file_sizes['badlyformed.xml'],
                        os.path.getsize(self.files['badlyformed.xml']),
                    'file with errors not modified by unitid_identifier script')


