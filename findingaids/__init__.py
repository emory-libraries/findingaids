# file findingaids/__init__.py
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

__version_info__ = (1, 0, 13, 'pre')

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
# TODO: update to use new render shortcut provided in newer versions of django
def render_with_context(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req, {'script_name': req.META['SCRIPT_NAME']})
    # Line below was an attempt to add script name to the context so I could
    # deal with template paths for the SITE_URL in a way that handled
    # apps being installed in a site subURL.
    # args[1]['script_name'] = req.META['SCRIPT_NAME']
    return render_to_response(*args, **kwargs)
