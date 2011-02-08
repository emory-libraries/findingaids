import feedparser
from recaptcha.client import captcha
from os import path

from django.test import Client, TestCase
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse

from eulcore.django.test import TestCase as EulDjangoTestCase

from findingaids.content import models, forms

class MockFeedParser:
    entries = []
    status = 200
    
    def parse(self, url):
        # construct a new feed result based on current entries & status
        feed = feedparser.FeedParserDict()
        feed['entries'] = self.entries
        feed.status = self.status
        return feed
    
class CachedFeedTest(TestCase):
    testid = 'testfeed'
    cache_key = 'rss-data-%s' % testid
    url = 'http://'
    
    def setUp(self):
        # replace feedparser module with a mock for testing
        self.mockfeedparser = MockFeedParser()   
        self._feedparser = models.feedparser
        models.feedparser = self.mockfeedparser
        
    def tearDown(self):
        # restore the real feedparser
        models.feedparser = self._feedparser
        # clear any feed data cached by tests
        cache.set(self.cache_key, None)

    def test_init_nocache(self):
        cf = models.CachedFeed(self.testid, self.url)
        self.assertEqual(None, cf._feed,
            'initial feed data should not be set on init when feed is not previously cached')

    def test_init_with_cache(self):
        # pre-populate the cache with test feed result
        cache.set(self.cache_key, self.mockfeedparser.parse(self.url))
        cf = models.CachedFeed(self.testid, self.url)
        self.assertNotEqual(None, cf._feed,
            'initial feed data should be set on init when feed is cached')

    def test_load_feed(self):
        data = ['a', 'b']
        self.mockfeedparser.entries = data
        cf = models.CachedFeed(self.testid, self.url)
        self.assert_(isinstance(cf.feed, feedparser.FeedParserDict),
            'feed property should be set from feedparse result')
        self.assert_(isinstance(cache.get(self.cache_key), feedparser.FeedParserDict),
            'feed data should be cached when loaded')

    def test_load_ifmodified(self):
        initial = ['a', 'b']
        self.mockfeedparser.entries = initial
        cf = models.CachedFeed(self.testid, self.url)
        cf.feed # access feed to load initial feed
        # change the data for comparison
        mod = ['z', 'y']
        self.mockfeedparser.entries = mod
        # set status to 304 Not Modified - new data should *not* be loaded
        self.mockfeedparser.status = 304
        self.assertEqual(initial, cf.items,
            'feed data should be unchanged when feed request returns 304 Not Modified')
        # set status to something besides 304 - new data should be loaded
        self.mockfeedparser.status = 200
        self.assertEqual(mod, cf.items,
            'feed data should be updated when feed request returns something besides 304')

    def test_items(self):
        myitems = ['news', 'update']
        self.mockfeedparser.entries = myitems

        cf = models.CachedFeed(self.testid, self.url)
        self.assertEqual(myitems, cf.items,
            'items property should be returned from feed entries')

    def test_clear_cache(self):
        # populate the cache with test feed result
        cache.set(self.cache_key, self.mockfeedparser.parse(self.url))
        cf = models.CachedFeed(self.testid, self.url)
        cf.clear_cache()
        self.assertEqual(None, cache.get(self.cache_key),
            'cached data should be None after calling clear_cache()')      

class ContentFeedTest(TestCase):

    def setUp(self):
        entry = feedparser.FeedParserDict()
        entry.title = 'About'
        entry.link = 'findingaids-about'
        entry.summary = 'some text'

        # replace feedparser module with a mock for testing
        self.mockfeedparser = MockFeedParser()
        self.mockfeedparser.entries = [entry]
        self._feedparser = models.feedparser
        models.feedparser = self.mockfeedparser

    def tearDown(self):
        # restore the real feedparser
        models.feedparser = self._feedparser
        # clear any feed data cached by tests
        models.ContentFeed().clear_cache()

    def test_get_entry(self):
        content = models.ContentFeed()
        # find test entry
        entry = content.get_entry('about')
        self.assertEqual('About', entry.title)
        # non-existent
        self.assertEqual(None, content.get_entry('bogus'))


class MockCaptcha:
    'Mock captcha client to allow testing without querying captcha servers'
    response = captcha.RecaptchaResponse(True)
    submit_args = {}
    display_arg = None

    def displayhtml(self, pubkey):
        self.display_arg = pubkey

    def submit(self, challenge, response, private_key, remote_ip):
        self.submit_args = {'challenge': challenge, 'response': response,
            'private_key': private_key, 'remote_ip': remote_ip}
        return self.response


class EmailTestCase(EulDjangoTestCase):
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
        self._captcha = forms.captcha
        forms.captcha = MockCaptcha()
        # set required captcha configs
        self._captcha_private_key = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', None)
        self._captcha_public_key = getattr(settings, 'RECAPTCHA_PUBLIC_KEY', None)
        self._captcha_theme = getattr(settings, 'RECAPTCHA_THEME', None)
        settings.RECAPTCHA_PRIVATE_KEY = 'mine & mine alone'
        settings.RECAPTCHA_PUBLIC_KEY = 'anyone can see this'
        settings.RECAPTCHA_THEME = ''

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
        forms.captcha = self._captcha
        # restore captcha settings
        if self._captcha_private_key is None:
            delattr(settings, 'RECAPTCHA_PRIVATE_KEY')
        else:
            settings.RECAPTCHA_PRIVATE_KEY = self._captcha_private_key
        if self._captcha_public_key is None:
            delattr(settings, 'RECAPTCHA_PUBLIC_KEY')
        else:
            settings.RECAPTCHA_PUBLIC_KEY = self._captcha_public_key
        if self._captcha_theme is None:
            delattr(settings, 'RECAPTCHA_THEME')
        else:
            settings.RECAPTCHA_THEME = self._captcha_theme

class FeedbackFormTest(EmailTestCase):
    
    exist_fixtures = {'files' : [
        path.join(path.dirname(path.abspath(__file__)), '..', 'fa', 'fixtures', 'abbey244.xml'),
    ]}

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
        feedback.is_valid()
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
        

    def test_captcha_challenge(self):
        feedback = forms.FeedbackForm()
        feedback.captcha_challenge()
        self.assertEqual(settings.RECAPTCHA_PUBLIC_KEY, forms.captcha.display_arg,
            'captcha challenge should be generated with public key from settings')
        
    def test_captcha_validation(self):
        # form data with message only
        data = {'message': 'something there',
            # captcha fields now required for form to be valid
            'recaptcha_challenge_field': 'boo',
            'recaptcha_response_field': 'hiss',
            }
        user_ip = '10.0.0.1'
        feedback = forms.FeedbackForm(data, remote_ip=user_ip)
        # validate
        self.assertTrue(feedback.is_valid())
        # check that captcha was submitted correctly
        self.assertEqual(data['recaptcha_challenge_field'],
            forms.captcha.submit_args['challenge'])
        self.assertEqual(data['recaptcha_response_field'],
            forms.captcha.submit_args['response'])
        self.assertEqual(settings.RECAPTCHA_PRIVATE_KEY,
            forms.captcha.submit_args['private_key'])
        self.assertEqual(user_ip, forms.captcha.submit_args['remote_ip'])

        # simulate invalid captcha response
        forms.captcha.response.is_valid = False
        forms.captcha.response.err_code = 'incorrect-captcha-sol'
        feedback = forms.FeedbackForm(data, remote_ip=user_ip)
        # validate
        self.assertFalse(feedback.is_valid(),
            'form should not be valid when captcha response is not valid')
        self.assert_('CAPTCHA response incorrect' in feedback.non_field_errors(),
            'captcha error should be included in non-field errors')

        # restore success response
        forms.captcha.response.is_valid = True
        forms.captcha.response.err_code = None


class ContentViewsTest(EmailTestCase):
    feed_entries = ['news', 'banner']
    exist_fixtures = {'files' : [
        path.join(path.dirname(path.abspath(__file__)), '..', 'fa', 'fixtures', 'abbey244.xml'),
    ]}

    def setUp(self):
        self.client = Client()
        # replace feedparser module with a mock for testing
        self.mockfeedparser = MockFeedParser()
        self.mockfeedparser.entries = self.feed_entries
        self._feedparser = models.feedparser
        models.feedparser = self.mockfeedparser
        super(ContentViewsTest, self).setUp()

    def tearDown(self):
        # restore the real feedparser
        models.feedparser = self._feedparser
        # clear any feed data cached by tests
        models.BannerFeed().clear_cache()
        models.NewsFeed().clear_cache()
        models.ContentFeed().clear_cache()
        super(ContentViewsTest, self).tearDown()

    def test_site_index_banner(self):
        index_url = reverse('site-index')
        response = self.client.get(index_url)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s'
                             % (expected, response.status_code, index_url))
        self.assertEqual(self.feed_entries, response.context['banner'],
            'feed entries should be set in template context as "banner"')

    def test_site_index_news(self):
        index_url = reverse('site-index')
        response = self.client.get(index_url)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s'
                             % (expected, response.status_code, index_url))
        self.assertEqual(self.feed_entries[0], response.context['news'],
            'first news feed entry should be set in template context as "news"')

    def test_site_index_no_news(self):
        self.mockfeedparser.entries = []        # simulate no entries in feed
        index_url = reverse('site-index')
        response = self.client.get(index_url)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s'
                             % (expected, response.status_code, index_url))
        self.assertEqual(None, response.context['news'],
            'news item should be None in template context when news feed has no items')

    def test_content_page(self):
        about = feedparser.FeedParserDict()
        about.title = 'About'
        about.link = 'findingaids-about'
        about.summary = 'some text'
        faq = feedparser.FeedParserDict()
        faq.title = 'FAQ'
        faq.link = 'findingaids-faq'
        faq.summary = 'other text'
        self.mockfeedparser.entries = [about, faq]

        content_url = reverse('content:page', args=['faq'])
        response = self.client.get(content_url)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s'
             % (expected, response.status_code, content_url))
        self.assertEqual(faq, response.context['page'],
            'feed item matching requested page is set in template context')
        self.assertPattern('<title>.*: %s.*</title>' % faq.title,
            response.content, msg_prefix='feed entry title should be set in html title')
        self.assertPattern('<h1[^>]*>.*%s.*</h1>' % faq.title,
            response.content, msg_prefix='feed entry title should be set as h1')

        # not found
        content_url = reverse('content:page', args=['bogus'])
        response = self.client.get(content_url)
        expected = 404
        self.assertEqual(response.status_code, expected, 
            'Expected %s but returned %s for %s (non-existent page)'
             % (expected, response.status_code, content_url))

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

        # test captcha theme setting
        settings.RECAPTCHA_THEME = None
        response = self.client.get(feedback_url)
        self.assertNotContains(response, 'var RecaptchaOptions',
            msg_prefix='feedback page should not contain Recaptcha Options when RECAPTCHA_THEME is not configured');
        settings.RECAPTCHA_THEME = 'white'
        response = self.client.get(feedback_url)
        self.assertContains(response, 'var RecaptchaOptions',
            msg_prefix='feedback page should contain Recaptcha Options when RECAPTCHA_THEME is configured');
        self.assertContains(response, "theme : 'white'",
            msg_prefix='feedback page should set configured RECAPTCHA_THEME in recaptcha theme option');

        # GET with an eadid
        response = self.client.get(feedback_url, {'eadid': 'abbey244'})
        self.assertPattern('Sending feedback about.*Abbey\s+Theatre\s+collection,\s+1921-1995',
            response.content,
            msg_prefix='feedback page should include title when sending feedback about a single ead');

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
        self.assertContains(response, 'here was an error sending your message',
            msg_prefix='response should display error message when sending email triggers an exception',
            status_code=500)