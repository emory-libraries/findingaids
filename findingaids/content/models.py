import feedparser
import logging

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__) 

class CachedFeed(object):
    '''RSS feed object with django caching.  When initialized, will load feed
    data from the django cache if it is available; whenever feed data is accessed,
    the feed data will be stored in the cache; and when checking for updated
    versions of the feed, takes advantage of :mod:`feedparser` features to use
    use ETag and Last-Modified and only refresh feed data when it has changed.

    You must specify an id to use as base cache key and a url where the RSS feed
    should be loaded.

    Designed to be easily extended, e.g.::

        class MyCustomFeed(CachedFeed):
            id = 'my-custom-feed'
            url = 'http://my.custom.url/feed.rss'

    '''

    def __init__(self, id=None, url=None):
        # NOTE: id and url are optional here to simplify extending this class
        # Things will fail if they are not set.  Better way to handle this?
        if id is not None:
            self.id = id
        if url is not None:
            self.url = url
        # error here if id or url are None?
        self._cache_key = 'rss-data-%s' % self.id

    @property
    def items(self):
        'List of items in a feed'
        return self.feed['items']

    @property
    def feed(self):
        'Feed result as returned from :meth:`feedparser.parse`'
        # attemp to initialize feed data from the django cache
        cached_feed = cache.get(self._cache_key)
        # if the feed is not cached, retrieve it
        if cached_feed is None:
            cached_feed = feedparser.parse(self.url)
        # if the feed was cached, check if it has changed since last retrieved
        else:
            # if the feed supports it, use etag & last-modified to only
            # grab content when it has changed
            opts = {}
            if hasattr(cached_feed, 'etag'):
                opts['etag'] = cached_feed.etag
            if hasattr(cached_feed, 'modified'):
                opts['modified'] = cached_feed.modified
            feed = feedparser.parse(self.url, **opts)
            # If status is anything but 304 (Not Modified), feed has
            # changed and we need to update with the latest content
            if getattr(feed, 'status', None) != 304:
                print 'DEBUG: feed has changed'
                cached_feed = feed

        # store latest version in the cache
        cache.set(self._cache_key, cached_feed)
        return cached_feed

    def clear_cache(self):
        'Clear any cached feed data'
        cache.set(self._cache_key, None)

class BannerFeed(CachedFeed):
    'Feed object to access configured RSS feed for home page banner images'
    id = 'banner'
    url = settings.CONTENT_RSS_FEEDS[id]

class NewsFeed(CachedFeed):
    'Feed object to access configured RSS feed for home page announcements'
    id = 'news'
    url = settings.CONTENT_RSS_FEEDS[id]

class ContentFeed(CachedFeed):
    'Feed object to access configured RSS feed for drupal-managed site content pages'
    id = 'content'
    url = settings.CONTENT_RSS_FEEDS[id]
    separator = '-'

    def get_entry(self, id):
        '''Get a single entry in the feed by a page identifier.  The identifier
        should match the portion of the item link after the first delimeter
        character (-).  For example, to match `findingaids-about`, you would
        search for `about`.

        Returns the feed entry if there is a match, or None if no match.
        '''
        for entry in self.items:
            prefix, sep, remainder = entry.link.partition(self.separator)
            if remainder == id:
                return entry
        