# file findingaids/fa/templatetags/ead.py
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

"""
Custom template filters for converting EAD tags to HTML.
"""

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from eulxml.xmlmap.eadmap import EAD_NAMESPACE

__all__ = ['format_ead']

register = template.Library()

XLINK_NAMESPACE = 'http://www.w3.org/1999/xlink'
EXIST_NAMESPACE = 'http://exist.sourceforge.net/NS/exist'

# render attributes which can be converted to simple tags
# - key is render attribute, value is tuple of start/end tag or
#   other start/end wrapping strings
rend_attributes = {
    'bold': ('<span class="ead-bold">', '</span>'),
    'italic': ('<span class="ead-italic">', '</span>'),
    'doublequote': ('"', '"'),
}

# tag names that can be converted to simple tags
# - key is tag name (with namespace), value is a tuple of start/end tag
simple_tags = {
    '{%s}emph' % EAD_NAMESPACE: ('<em>', '</em>'),
    '{%s}title' % EAD_NAMESPACE: ('<span class="ead-title">', '</span>'),
    '{%s}match' % EXIST_NAMESPACE: ('<span class="exist-match">', '</span>'),
}


def format_extref(node):
    url = node.get('{%s}href' % XLINK_NAMESPACE)
    href = ' href="%s"' % url if url is not None else ''
    return ('<a%s>' % href, '</a>')

# more complex tags
# - key is tag name, value is a callable that takes a node
other_tags = {
    '{%s}extref' % EAD_NAMESPACE: format_extref,
}


@register.filter(needs_autoescape=True)
def format_ead(value, autoescape=None):
    """
    Custom django filter to convert structured fields in EAD objects to
    HTML. :class:`~eulcore.xmlmap.XmlObject` values are recursively
    processed, escaping text nodes and converting elements to <span> objects
    where appropriate. Other values are simply converted to unicode and
    escaped.

    Currently performs the following conversions:
      * elements with ``@render="doublequote"`` are wrapped in double quotes
        after stripping the element
      * elements with ``@render="bold"`` are replaced with ``<span
        class="ead-bold">``
      * elements with ``@render="italic"`` are replaced with ``<span
        class="ead-italic"``
      * ``<emph>`` elements are replaced with ``<em>``
      * ``<title>`` elements are replaced with ``<span class="ead-title">``
      * other elements are stripped
      * text nodes are HTML escaped where the template context calls for it
    """

    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x

    if hasattr(value, 'node'):
        result = format_ead_node(value.node, esc)
    else:
        result = ''

    return mark_safe(result)


def format_ead_node(node, escape):
    '''Recursive method to generate HTML with the text and any
    formatting for the contents of an EAD node.

    :param node: lxml element or node to be converted from EAD to HTML
    :param escape: template escape method to be used on node text content
    :returns: string with the HTML output
    '''

    # list of strings to be populated
    result = []

    # include any text directly in this node, before the first child
    if node.text is not None:
        result.append(escape(node.text))

    for el in node.iterchildren():
        # check for supported render attributes
        rend = el.get('render', None)
        if rend is not None and rend in rend_attributes.keys():
            start, end = rend_attributes[rend]

        # simple tags that can be converted to html markup
        elif el.tag in simple_tags.keys():
            start, end = simple_tags[el.tag]

        # more complex tags
        elif el.tag in other_tags.keys():
            start, end = other_tags[el.tag](el)

        # unsupported tags that do not get converted
        else:
            start, end = '', ''

        # wrap the node with start/end tags and recurse
        result.append(''.join([start, format_ead_node(el, escape), end,
                               escape(el.tail or '')]))

    return ''.join(result)
