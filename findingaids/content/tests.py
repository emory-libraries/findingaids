import feedparser

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


class EmailTestCase(TestCase):
    # common test class with logic to mock sending mail for tests
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
        # set required config settings here too
        self._server_email = getattr(settings, 'SERVER_EMAIL', None)
        self._email_prefix = getattr(settings, 'EMAIL_SUBJECT_PREFIX', None)
        self._feedback_email = getattr(settings, 'FEEDBACK_EMAIL', None)
        settings.SERVER_EMAIL = self.server_email
        settings.EMAIL_SUBJECT_PREFIX = self.email_prefix
        settings.FEEDBACK_EMAIL = self.feedback_email

    def tearDown(self):
        # restore real send_mail
        forms.send_mail = self._send_mail
        if self._server_email is None:
            delattr(settings, 'SERVER_EMAIL')
        else:
            settings.SERVER_EMAIL = self._server_email
        if self._email_prefix is None:
            delattr(settings.EMAIL_SUBJECT_PREFIX)
        else:
            settings.EMAIL_SUBJECT_PREFIX = self._email_prefix
        if self._feedback_email is None:
            delattr(settings.feedback_email)
        else:
            settings.FEEDBACK_EMAIL = self._feedback_email


class FeedbackFormTest(EmailTestCase):

    def setUp(self):
        super(FeedbackFormTest, self).setUp()

    def tearDown(self):
        super(FeedbackFormTest, self).tearDown()

    def test_send_email(self):
        # form data with message only
        txt = 'here is my 2 cents'
        data = {'message': 'here is my 2 cents'}
        feedback = forms.FeedbackForm(data)
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
            'when email is specified on form, email should come user-entered from email address')

        # message + email address + name
        user_name = 'Me Myself'
        data.update({'name': user_name})
        feedback = forms.FeedbackForm(data)
        # confirm form is valid, propagate cleaned data
        self.assertTrue(feedback.is_valid())
        # simulate sending an email
        self.assertTrue(feedback.send_email())
        self.assertEqual('"%s" <%s>' % (user_name, user_email), self.sent_mail['from'],
            'when email & name are specified on form, email should come user-entered from email address with name')


class ContentViewsTest(EulDjangoTestCase, EmailTestCase):
    feed_entries = ['news', 'banner']

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

        # POST - send an email
        response = self.client.post(feedback_url, {'message': 'more please'})
        expected = 200
        self.assertEqual(response.status_code, expected,
            'Expected %s but returned %s for POST on %s'
             % (expected, response.status_code, feedback_url))
        self.assertContains(response, 'feedback has been sent',
            msg_prefix='Thank you message should be displayed on result page after sending feedback')

        # POST - simulate error sending email
        self.simulate_email_exception()
        response = self.client.post(feedback_url, {'message': 'more please'})
        expected = 500
        self.assertEqual(expected, response.status_code, 
            'Expected %s but returned %s for POST on %s'
             % (expected, response.status_code, feedback_url))
        self.assertContains(response, 'here was an error sending your message',
            msg_prefix='response should display error message when sending email triggers an exception',
            status_code=500)