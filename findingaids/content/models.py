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
    _feed = None

    def __init__(self, id=None, url=None):
        # NOTE: id and url are optional here to simplify extending this class
        # Things will fail if they are not set.  Better way to handle this?
        if id is not None:
            self.id = id
        if url is not None:
            self.url = url
        # error here if id or url are None?
        self._cache_key = 'rss-data-%s' % id

        # initialize feed data from the django cache, if available
        cached_feed = cache.get(self._cache_key)
        if cached_feed is not None:
            self._feed = cached_feed

    @property
    def items(self):
        'List of items in a feed'
        return self.feed['items']

    @property
    def feed(self):
        'Feed result as returned from :meth:`feedparser.parse`'
        if self._feed is None:
            self._feed = feedparser.parse(self.url)
        else:
            # if the feed supports it, use etag & last-modified to only
            # grab content when it has changed
            opts = {}
            if hasattr(self._feed, 'etag'):
                opts['etag'] = self._feed.etag
            if hasattr(self._feed, 'modified'):
                opts['modified'] = self._feed.modified
            feed = feedparser.parse(self.url, **opts)
            # If status is anything but 304 (Not Modified), feed has
            # changed and we need to update with the latest content
            if getattr(feed, 'status', None) != 304:
                self._feed = feed

        # store latest version in the cache
        cache.set(self._cache_key, self._feed)
        return self._feed

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