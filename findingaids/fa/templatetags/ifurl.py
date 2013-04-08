# file findingaids/fa/templatetags/ifurl.py
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

from django import template
from django.template.base import TemplateSyntaxError
from django.template.defaulttags import url, URLNode

register = template.Library()


class IfURLNode(URLNode):
    def __init__(self, condition, viewname_if, viewname_ifnot, args, kwargs, asvar):
        # store condition variable and alternate view
        self.condition = condition
        self.viewname_if = viewname_if
        # default to view if condition is false; override in render
        super(IfURLNode, self).__init__(viewname_ifnot, args, kwargs, asvar)

    def render(self, context):
        # get the current value of condition in template context, update viewname if needed
        condition = context[self.condition]
        if condition:
            self.view_name = self.viewname_if
        # let URLNode class do all the real work
        return super(IfURLNode, self).render(context)


@register.tag
def ifurl(parser, token):
    """
    Customized version of Django's template tag *url*.

    Takes a condition and two view names, followed by any arguments taken by url.
    If the condition is true, will render the url with the first view name
    specified, otherwise will use the second.

    For example::

       {% ifurl preview 'preview:doc' 'main:doc' arg1=foo %}

    When preview is true in the template context, url will be generated as
    preview:doc, otherwise it will be generated as main:doc.
    """
    parts = token.contents.split()
    condition = parts[1]
    remainder = parts[4:]

    # as of django 1.5, view name must be quoted strings
    try:
        name_if = parser.compile_filter(parts[2])
        name_ifnot = parser.compile_filter(parts[3])
    except TemplateSyntaxError as exc:
        exc.args = (exc.args[0] + ". "
                    "The syntax of 'ifurl' update to match 'url' change " +
                    "in Django 1.5; see the docs."),

    # construct a normal-looking url token
    # - allow django url templatetag to do all the argument parsing
    token.contents = "url %s %s" % (name_if, ' '.join(remainder))
    urlnode = url(parser, token)
    # url returns a URLNode - use arguments set on that node to init custom IfURLNode
    return IfURLNode(condition, name_if, name_ifnot, urlnode.args, urlnode.kwargs,
                     urlnode.asvar)

