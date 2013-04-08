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

__all__ = ['format_ead', 'format_ead_names']

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

EAD_PERSNAME = '{%s}persname' % EAD_NAMESPACE
EAD_CORPNAME = '{%s}corpname' % EAD_NAMESPACE
EAD_GEOGNAME = '{%s}geogname' % EAD_NAMESPACE

name_tags = {
    EAD_PERSNAME: 'schema:Person',
    EAD_CORPNAME: 'schema:Organization',
    EAD_GEOGNAME: 'schema:Place',
}


def format_nametag(node):
    rdftype = name_tags.get(node.tag, None)

    # if not a supported type, don't tag at all
    if rdftype is None:
        return ('', '')

    about = ''
    uri = None
    if node.get('authfilenumber') is not None:
        authnum = node.get('authfilenumber')
        if node.get('source') == 'viaf':
            uri = 'http://viaf.org/%s/' % authnum
        elif node.get('source') == 'geonames':
            uri = 'http://sws.geonames.org/%s/' % authnum
        elif node.get('source') == 'dbpedia':
            uri = 'http://dbpedia.org/resource/%s/' % authnum

        if uri is not None:
            about = ' about="%s"' % uri

    start = '<span%s typeof="%s"><span property="schema:name">' % \
            (about, rdftype)
    end = '</span></span>'

    # NOTE: *preliminary* role  / relation to context
    rel = None
    if node.get('role') is not None:
        rel = node.get('role')
        rel = 'schema:' + rel.replace('originator:', '')
    elif rdftype == 'schema:Organization':
        # NOTE: this should not be set for control access orgs
        rel = 'schema:affiliation'

    # special case: for controlaccess, we can infer name from encodinganalog
    if node.getparent().tag == '{%s}controlaccess' % EAD_NAMESPACE:
        encodinganalog = node.get('encodinganalog')
        if node.tag == EAD_PERSNAME and encodinganalog == '700' or \
           node.tag == EAD_CORPNAME and encodinganalog == '710':
            rel = 'schema:contributor'
        elif node.tag == EAD_PERSNAME and encodinganalog == '600' or \
                node.tag == EAD_CORPNAME and encodinganalog in ['610', '611'] or \
                node.tag == EAD_GEOGNAME and encodinganalog == '651':
            rel = 'schema:about'

        # for now, assume about if we can't otherwise determine
        # *could* soften this to just schema:mentions
        else:
            rel = 'schema:about'

    # if nothing else, the document obviously mentions this entity
    if rel is None:
        rel = 'schema:mentions'

    if rel is not None:
        start = '<span rel="%s">%s' % (rel, start)
        end += '</span>'

    return (start, end)


@register.filter(needs_autoescape=True)
def format_ead(value, autoescape=None, names=False):
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
        result = format_ead_node(value.node, esc, names)
    else:
        result = ''

    return mark_safe(result)


@register.filter(needs_autoescape=True)
def format_ead_names(value, autoescape=None):
    return format_ead(value, autoescape, names=True)


def format_ead_node(node, escape, names=False):
    '''Recursive method to generate HTML with the text and any
    formatting for the contents of an EAD node.

    :param node: lxml element or node to be converted from EAD to HTML
    :param escape: template escape method to be used on node text content
    :returns: string with the HTML output
    '''
    # find any start/end tags for the current element

    # check for supported render attributes
    rend = node.get('render', None)
    if rend is not None and rend in rend_attributes.keys():
        start, end = rend_attributes[rend]

    # simple tags that can be converted to html markup
    elif node.tag in simple_tags.keys():
        start, end = simple_tags[node.tag]

    # more complex tags
    elif node.tag in other_tags.keys():
        start, end = other_tags[node.tag](node)

    # convert names to semantic web / rdfa if requested
    elif names and node.tag in name_tags.keys():
        start, end = format_nametag(node)

    # unsupported tags that do not get converted
    else:
        start, end = '', ''

    # list of text contents to be compiled
    contents = [start]  # start tag
    # include any text directly in this node, before the first child
    if node.text is not None:
        contents.append(escape(node.text))

    # format any child nodes and add to the list of text
    contents.extend([format_ead_node(el, escape=escape, names=names)
                     for el in node.iterchildren()])

    # end tag for this node + any tail text
    contents.extend([end, escape(node.tail or '')])

    return ''.join(contents)
