import feedparser

from django.test import Client, TestCase 
from django.core.cache import cache
from django.core.urlresolvers import reverse

from eulcore.django.test import TestCase as EulDjangoTestCase

from findingaids.content import models

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


class ContentViewsTest(EulDjangoTestCase):
    feed_entries = ['news', 'banner']

    def setUp(self):
        self.client = Client()
        # replace feedparser module with a mock for testing
        self.mockfeedparser = MockFeedParser()
        self.mockfeedparser.entries = self.feed_entries
        self._feedparser = models.feedparser
        models.feedparser = self.mockfeedparser

    def tearDown(self):
        # restore the real feedparser
        models.feedparser = self._feedparser
        # clear any feed data cached by tests
        models.BannerFeed().clear_cache()
        models.NewsFeed().clear_cache()
        models.ContentFeed().clear_cache()

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


