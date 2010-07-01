'''
"The ornaments of a house are the friends who visit it."
- Ralph Waldo Emmerson
'''

#THIS IS DUPLICATE CODE FROM DWRANGLER AND SHOULD EVENTUALLY BE MOVED INTO EULCORE

from mimeparse import mimeparse

from django.shortcuts import get_object_or_404
from findingaids import render_with_context

# Custom Decorators because they are so very pretty.

MIME_TYPE = {
    'rss': ['application/rss+xml', 'text/xml'],
    'json': ['application/json', 'text/json'],
    'atom': ['application/atom+xml', 'text/xml'],
    'rdf': ['application/rdf+xml'],
    'html': ['text/html'],
}

FORMAT_MAP = {
    'html': 'text/html',
    'json': 'application/json',
    'xml': 'text/xml',
    'rss': 'application/rss+xml',
    'atom': 'application/atom+xml',
    'rdf': 'application/rdf+xml',
}

def format_req(fmt, new_fn):
    '''
    Provides compatability with URLs from things like wordpress that
    request content type via a querystring param like '?format=rss'

    :param fmt: String indicating format to return new_fn for.
    :param new_fn: Bound method to return if format querystring matches format.

    '''

    def _decorator(view_fn):
        def _wraped(request, *args, **kwargs):
            if request.GET.get('format', None) == fmt:
                return new_fn(request, *args, **kwargs)
            # Default to returning the original method
            return view_fn(request, *args, **kwargs)
        return _wraped
    return _decorator

def content_neg(fmt_dict):
    """
    Provides basic content negotiation and returns a view method based on the
    best match of content types as indicated in fmt_dct.

    :param fmt_dict: dictionary of content type and return method pairs.

    for example::
        def rdf_view(request, arg):
            return RDF_RESONSE

        @content_neg({'application/rdf+xml': rdf_view})
        def html_view(request, arg):
            return HTML_RESONSE

    The above example would return the rdf_view on a request type of
    'application/rdf+xml' or the normal view if anything else.

    """
    def _decorator(view_fn):
        def _wrapped(request, *args, **kwargs):
            default_type = 'text/html'  # If not specificied assume HTML request.

            # Add text/html for the original method if not already included.
            if default_type not in fmt_dict:
                fmt_dict[default_type] = view_fn

            try:
                req_type = request.META['HTTP_ACCEPT']
                # print "REQEUEST TYPE %s" % req_type
            except KeyError:
                req_type = default_type
                # print "NO HTTP_ACCEPT VAR!!!!!"

            # Get the best match for the content type requested.
            content_type = mimeparse.best_match(fmt_dict.keys(),
                                                req_type)
            # print "CONTENT TYPE MATCH %s" % content_type
            # Return the view matching content type or the orignal view
            # if no match.
            if not content_type or content_type not in fmt_dict:
                return view_fn(request, *args, **kwargs)
            return fmt_dict[content_type](request, *args, **kwargs)
        return _wrapped
    return _decorator

# These two methods based on # http://www.djangosnippets.org/snippets/254/
def user_or_owner_test_with_403(test_fn, model):
    '''
    Decorator tests if the user has a permission or is owner of a model object
    instance.

    Anonymous users will be redirected to login_url, while users that fail
    the test will be given a 403 error.

    :param test_fn:  Permissions test function.  Normally a lambda function.
    :param model:  Model to retrieve to do an ownership test of.
    
    '''
    def _wrapped(view_fn):
        def _owner_or_perm(request, * args, ** kwargs):
            '''
            Returns boolean if user has permission OR is owner.

            :param view_fn: The wrapped method to continue onto if passes.
            
            '''

            if 'project_slug' in kwargs:
                obj = get_object_or_404(model, slug=kwargs['slug'], project_fk__slug=kwargs['project_slug'])
            else:
                obj = get_object_or_404(model, slug=kwargs['slug'])

            if obj.is_owner(request.user): # Check for owner
                return True
            if test_fn(request.user): # Check of user permissions
                return True
            return False

        def _routeReturn(request, * args, ** kwargs):
            '''
            Handles the return depending on that status of the user and object requested.
            
            '''
            if _owner_or_perm(request, * args, ** kwargs): # Return normal view function if true.
                return view_fn(request, * args, ** kwargs)
            resp = render_with_context(request, '403.html')
            resp.status_code = 403
            return resp
        
        return _routeReturn

    return _wrapped

def has_perm_or_owner_of(perm, model):
    '''
    Decorator for views that checks weather a user has a particular permission
    enabled or is the owner of the instance.  redirects to a login page or
    renders a 403 as necessary.

    :param perm: Permission test to use for the logged in user.
    :param model: Model to retrieve for an ownership test.
    
    '''
    return user_or_owner_test_with_403(lambda u: u.has_perm(perm), model)

def user_passes_test_or_403(test_fn):
    '''
    Decorator for views that checks for permission and returns 403 if none.

    :param test_fn: Permissions test function, usually a lambda function.
    
    '''
    def _wrapped(view_fn):
        def _dec(request, * args, ** kwargs):
            if test_fn(request.user):
                return view_fn(request, * args, ** kwargs)
            resp = render_with_context(request, '403.html')
            resp.status_code = 403
            return resp
        return _dec
    
    return _wrapped