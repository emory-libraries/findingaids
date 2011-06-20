__version_info__ = (1, 0, 8, 'pre'

# Dot-connect all but the last. Last is dash-connected if not None.
__version__ = '.'.join(str(i) for i in __version_info__[:-1])
if __version_info__[-1] is not None:
    __version__ += ('-%s' % (__version_info__[-1],))


#THIS IS DUPLICATE CODE FROM DWRANGLER AND SHOULD EVENTUALLY BE MOVED INTO EULCORE
# Extends the normal render_to_response to include RequestContext objects.
# Taken from http://www.djangosnippets.org/snippets/3/
# Other similar implementations and adaptations http://lincolnloop.com/blog/2008/may/10/getting-requestcontext-your-templates/
# I also added the SCRIPT_NAME to dictionary so it would be available to templates
# Since I always uset his for this application it makes sense for this app but
# I'm unsure this is the best way overall.
def render_with_context(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req, {'script_name': req.META['SCRIPT_NAME']})
    # Line below was an attempt to add script name to the context so I could
    # deal with template paths for the SITE_URL in a way that handled
    # apps being installed in a site subURL.
    # args[1]['script_name'] = req.META['SCRIPT_NAME']
    return render_to_response(*args, **kwargs)
