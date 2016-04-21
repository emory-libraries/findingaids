# file findingaids/content/tests.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from os import path
from unittest import skip

from django.test import Client
from django.conf import settings
from django.core.urlresolvers import reverse

from eulexistdb.testutil import TestCase as EulexistdbTestCase
from eullocal.django.forms.tests import MockCaptcha

from findingaids.content import forms
from findingaids.fa.models import Archive

# re-using finding aid fixtures from main fa app
exist_fixture_path = path.join(path.dirname(path.abspath(__file__)), '..',
    'fa', 'tests', 'fixtures')


class EmailTestCase(EulexistdbTestCase):
    # Common test class with logic to mock sending mail and mock captcha submission
    # to test functionality without actual sending email or querying captcha servers.
    # Extending EulDjangoTestCase to allow use of eXist fixtures
    server_email = 'admin@findingaids.library.emory.edu'
    email_prefix = '[FA] '
    feedback_email = ('fa-admin@emory.edu',)
    _sent_mail = {}
    _mail_exception = None

    @property
    def sent_mail(self):
        'Access parameters passed to last send_mail call'
        return EmailTestCase._sent_mail

    def simulate_email_exception(self):
        'Simulate an exception on the next send_mail call via mock send_mail'
        EmailTestCase._mail_exception = Exception

    @staticmethod
    def _mock_send_mail(subject, message, from_email, recipient_list, **kwargs):
        if EmailTestCase._mail_exception is not None:
            ex = EmailTestCase._mail_exception
            EmailTestCase._mail_exception = None
            raise ex

        # store values for tests to inspect
        EmailTestCase._sent_mail = {'subject': subject, 'message': message,
            'from': from_email, 'recipients': recipient_list}
        EmailTestCase._sent_mail.update(**kwargs)
        return 1    # simulate success (django send_mail returns 1)

    def setUp(self):
        # swap out send_mail with mock function for testing
        self._send_mail = forms.send_mail
        forms.send_mail = self._mock_send_mail
        # set required email config settings
        self._server_email = getattr(settings, 'SERVER_EMAIL', None)
        self._email_prefix = getattr(settings, 'EMAIL_SUBJECT_PREFIX', None)
        self._feedback_email = getattr(settings, 'FEEDBACK_EMAIL', None)
        settings.SERVER_EMAIL = self.server_email
        settings.EMAIL_SUBJECT_PREFIX = self.email_prefix
        settings.FEEDBACK_EMAIL = self.feedback_email

        # swap out captcha with mock
        self._captcha = forms.captchafield.captcha
        forms.captchafield.captcha = MockCaptcha()
        # set required captcha configs
        self._captcha_private_key = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', None)
        self._captcha_public_key = getattr(settings, 'RECAPTCHA_PUBLIC_KEY', None)
        settings.RECAPTCHA_PRIVATE_KEY = 'mine & mine alone'
        settings.RECAPTCHA_PUBLIC_KEY = 'anyone can see this'

    def tearDown(self):
        # restore real send_mail
        forms.send_mail = self._send_mail
        # restore email settings
        if self._server_email is None:
            delattr(settings, 'SERVER_EMAIL')
        else:
            settings.SERVER_EMAIL = self._server_email
        if self._email_prefix is None:
            delattr(settings.EMAIL_SUBJECT_PREFIX)
        else:
            settings.EMAIL_SUBJECT_PREFIX = self._email_prefix
        if self._feedback_email is None:
            delattr(settings, 'FEEDBACK_EMAIL')
        else:
            settings.FEEDBACK_EMAIL = self._feedback_email

        # restore real captcha
        forms.captchafield.captcha = self._captcha
        # restore captcha settings
        if self._captcha_private_key is None:
            delattr(settings, 'RECAPTCHA_PRIVATE_KEY')
        else:
            settings.RECAPTCHA_PRIVATE_KEY = self._captcha_private_key
        if self._captcha_public_key is None:
            delattr(settings, 'RECAPTCHA_PUBLIC_KEY')
        else:
            settings.RECAPTCHA_PUBLIC_KEY = self._captcha_public_key

class FeedbackFormTest(EmailTestCase):

    exist_fixtures = {'files' : [path.join(exist_fixture_path, 'abbey244.xml')]}

    def setUp(self):
        super(FeedbackFormTest, self).setUp()

    def tearDown(self):
        super(FeedbackFormTest, self).tearDown()

    def test_send_email(self):
        # form data with message only
        txt = 'here is my 2 cents'
        data = {'message': 'here is my 2 cents',
            # captcha fields now required for form to be valid
            'recaptcha_challenge_field': 'boo',
            'recaptcha_response_field': 'hiss',
            }
        feedback = forms.FeedbackForm(data, remote_ip='0.0.0.0')
        # confirm form is valid, propagate cleaned data
        self.assertTrue(feedback.is_valid())
        # simulate sending an email
        self.assertTrue(feedback.send_email())
        self.assert_(txt in self.sent_mail['message'],
            'form message value should be included in email text body')
        self.assert_(self.sent_mail['subject'].startswith(self.email_prefix),
            'email subject should start with configured email prefix')
        self.assertEqual(self.server_email, self.sent_mail['from'],
            'when email is not specified on form, email should come from configured email address')
        self.assertEqual(self.feedback_email, self.sent_mail['recipients'],
            'feedback email should be sent to configured email recipients')

        # message + email address
        user_email = 'me@my.domain.com'
        data.update({'email': user_email})
        feedback = forms.FeedbackForm(data)
        # confirm form is valid, propagate cleaned data
        self.assertTrue(feedback.is_valid())
        # simulate sending an email
        self.assertTrue(feedback.send_email())
        self.assertEqual(user_email, self.sent_mail['from'],
            'when email is specified on form, email should come from user-entered from email address')
        self.assert_(user_email in self.sent_mail['message'],
            'when email is specified on form, it should be included in message text')

        # message + email address + name
        user_name = 'Me Myself'
        data.update({'name': user_name})
        feedback = forms.FeedbackForm(data)
        # confirm form is valid, propagate cleaned data
        self.assertTrue(feedback.is_valid())
        # simulate sending an email
        self.assertTrue(feedback.send_email())
        self.assertEqual('"%s" <%s>' % (user_name, user_email), self.sent_mail['from'],
            'when email & name are specified on form, email should come from user-entered from email address with name')
        self.assert_(user_name in self.sent_mail['message'],
            'when name is specified on form, it should be included in message text')

        # send message with optional eadid & url
        eadid = 'abbey244'
        ead_url = reverse('fa:findingaid', args=[eadid])
        data.update({'eadid': eadid, 'url': ead_url})
        feedback = forms.FeedbackForm(data)
        # confirm form is valid, propagate cleaned data
        self.assertTrue(feedback.is_valid())
        # simulate sending an email
        self.assertTrue(feedback.send_email())
        self.assert_(eadid in self.sent_mail['message'],
            'when eadid is specified in form data, it should be included in message text')
        self.assert_('Abbey Theatre collection, 1921-1995' in self.sent_mail['message'],
            'when eadid is specified on form, ead title should be included in message text')
        self.assert_(ead_url in self.sent_mail['message'],
            'when url is specified on form, it should be included in message text')

# disabling tests here because request materials form is no longer used
# (superseded by aeon)


class RequestMaterialsFormTest(EmailTestCase):

    def setUp(self):
        super(RequestMaterialsFormTest, self).setUp()

    def tearDown(self):
        super(RequestMaterialsFormTest, self).tearDown()

    @skip
    def test_send_email(self):
        # form data with message only
        data = {
            'repo': [settings.REQUEST_MATERIALS_CONTACTS[0][0]],
            'name': 'A. Scholar',
            'date': 'tomorrow',
            'email': 'a.scholar@gmail.com',
            'phone': '7-1234',
            'request': 'MSS644 Ted Hughes Box 1 Box 5 OP12',
            # captcha fields now required for form to be valid
            'recaptcha_challenge_field': 'boo',
            'recaptcha_response_field': 'hiss',
            'remote_ip': '0.0.0.0',
        }

        feedback = forms.RequestMaterialsForm(data)
        # confirm form is valid, propagate cleaned data
        self.assertTrue(feedback.is_valid())

        # simulate sending an email
        self.assertTrue(feedback.send_email())
        self.assertPattern('Name:\s+%s' % data['name'], self.sent_mail['message'],
            'name submitted on form should be included in email text')
        self.assertPattern('Date of Visit:\s+%s' % data['date'], self.sent_mail['message'],
            'date of visit submitted on form should be included in email text')
        self.assertPattern('Phone Number:\s+%s' % data['phone'], self.sent_mail['message'],
            'phone number submitted on form should be included in email text')
        self.assert_(data['request'] in self.sent_mail['message'],
            'text of materials requested on form should be included in email text')
        self.assert_(data['email'] in self.sent_mail['from'],
            'material request email should come from user-entered from email address')
        self.assert_(data['name'] in self.sent_mail['from'],
            'material request email should come from user-entered from name')


class ContentViewsTest(EmailTestCase):
    exist_fixtures = {'files': [path.join(exist_fixture_path, 'abbey244.xml')]}
    fixtures = ['archive_contacts.json', 'contacts.json']

    def setUp(self):
        self.client = Client()
        super(ContentViewsTest, self).setUp()

    def test_site_index_banner(self):
        index_url = reverse('site-index')
        response = self.client.get(index_url)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s'
                             % (expected, response.status_code, index_url))

    def test_feedback_form(self):
        # GET - display the form
        feedback_url = reverse('content:feedback')
        response = self.client.get(feedback_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
            'Expected %s but returned %s for GET on %s'
             % (expected, response.status_code, feedback_url))
        self.assert_(isinstance(response.context['form'], forms.FeedbackForm),
            'feedback form should be set in template context for GET on %s' % feedback_url)
        self.assertNotContains(response, 'noindex,nofollow',
             msg_prefix='default feedback page should not include noindex,nofollow bots directive')
        self.assertNotContains(response, 'link rel="canonical"',
             msg_prefix='default feedback page should not include link rel=canonical')

        # GET with an eadid
        response = self.client.get(feedback_url, {'eadid': 'abbey244'})
        self.assertPattern('Sending feedback about.*Abbey\s+Theatre\s+collection,\s+1921-1995',
            response.content,
            msg_prefix='feedback page should include title when sending feedback about a single ead')
        self.assertContains(response, ': Feedback on Abbey Theatre collection',
            msg_prefix='html header should differentiate from default feedback page')
        self.assertContains(response, 'noindex,nofollow',
            msg_prefix='item feedback page should include noindex, no follow bots directive')
        self.assertContains(response, 'link rel="canonical"',
             msg_prefix='item feedback page should include link to canonical feedback page')

        # POST - send an email
        feedback_data = {
            'message': 'more please',
            # captcha fields now required for form to be valid
            'recaptcha_challenge_field': 'knock knock',
            'recaptcha_response_field': 'whos there',
        }
        response = self.client.post(feedback_url, feedback_data)
        expected = 200
        self.assertEqual(response.status_code, expected,
            'Expected %s but returned %s for POST on %s'
             % (expected, response.status_code, feedback_url))
        self.assertContains(response, 'feedback has been sent',
            msg_prefix='Thank you message should be displayed on result page after sending feedback')

        # POST - simulate error sending email
        self.simulate_email_exception()
        response = self.client.post(feedback_url, feedback_data)
        expected = 500
        self.assertEqual(expected, response.status_code,
            'Expected %s but returned %s for POST on %s'
             % (expected, response.status_code, feedback_url))
        self.assertContains(response, 'here was an error sending your feedback',
            msg_prefix='response should display error message when sending email triggers an exception',
            status_code=500)

    def test_request_materials(self):
        # NOTE: this is a test for request_materials page
        # The PT ID is #117174547

        # GET - display the form
        rqst_materials_url = reverse('content:request-materials')
        response = self.client.get(rqst_materials_url)
        expected = 200
        self.assertEqual(response.status_code, expected,
            'Expected %s but returned %s for GET on %s'
             % (expected, response.status_code, rqst_materials_url))

        '''Check if the MARBL archive has two contacts'''
        self.assertEqual(Archive.objects.get(label="MARBL").contacts.count(), 2)

        '''Check if the EUA archive has two contacts'''
        self.assertEqual(Archive.objects.get(label="EUA").contacts.count(), 3)

        '''Check if the Pitts archive has zero contacts'''
        self.assertEqual(Archive.objects.get(label="Pitts").contacts.count(), 0)

        '''Check if the MARBL contains the contact name "test1"'''
        self.assertEqual(Archive.objects.get(label="MARBL").contacts.filter(username="test1").count(), 1)

        '''Check if the EUA contains the contact name "test2"'''
        self.assertEqual(Archive.objects.get(label="EUA").contacts.filter(username="test2").count(), 1)

        '''Check if a user without names would be displayed on request materials page with email "test5@domain.com"'''
        self.assertContains(response, '<a href="mailto:test5@domain.com">test5@domain.com</a>', html=True)

    #
    # @skip
    # def test_request_materials(self):
    #     # NOTE: this test has been disabled because the request materials edit
    #     # form has been disabled as the archives transition to using Aeon
    #     # for requesting materials
    #
    #     # GET - display the form
    #     rqst_materials_url = reverse('content:request-materials')
    #     response = self.client.get(rqst_materials_url)
    #     expected = 200
    #     self.assertEqual(response.status_code, expected,
    #         'Expected %s but returned %s for GET on %s'
    #          % (expected, response.status_code, rqst_materials_url))
    #     self.assert_(isinstance(response.context['form'], forms.RequestMaterialsForm),
    #         'request materials form should be set in template context for GET on %s' % rqst_materials_url)
    #
    #     # POST - send an email
    #     data = {
    #         'repo': [settings.REQUEST_MATERIALS_CONTACTS[0][0]],
    #         'name': 'A. Scholar',
    #         'date': 'tomorrow',
    #         'email': 'a.scholar@gmail.com',
    #         'phone': '7-1234',
    #         'request': 'MSS644 Ted Hughes Box 1 Box 5 OP12',
    #         # captcha fields required for form to be valid
    #         'recaptcha_challenge_field': 'boo',
    #         'recaptcha_response_field': 'hiss',
    #         'remote_ip': '0.0.0.0',
    #     }
    #     response = self.client.post(rqst_materials_url, data)
    #     expected = 200
    #     self.assertEqual(response.status_code, expected,
    #         'Expected %s but returned %s for POST on %s'
    #          % (expected, response.status_code, rqst_materials_url))
    #     self.assertContains(response, 'request for materials has been sent',
    #         msg_prefix='success message should be displayed on result page after sending feedback')
