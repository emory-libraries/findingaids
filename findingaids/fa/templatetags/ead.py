"""
Custom filters for processing EAD structured fields to HTML.
"""

from lxml import etree

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

__all__ = [ 'format_ead', 'format_ead_children' ]

register = template.Library()

@register.filter
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
        escape = conditional_escape
    else:
        escape = lambda x: x
    
    if value is None:
        parts = []
    elif hasattr(value, 'dom_node'):
        parts = node_parts(value.dom_node, escape, include_tail=False)
    else:
        parts = [ escape(unicode(value)) ]
    
    result = ''.join(parts)
    return mark_safe(result)
format_ead.needs_autoescape = True

@register.filter
def format_ead_children(value, autoescape=None):
    """
    Custom django filter to convert structured fields in EAD objects to
    HTML. Follows the same logic as :func:`format_ead`, but processes only
    the children of the top-level XmlObject, ignoring rendering indicators
    on the top-level element itself.
    """

    if autoescape:
        escape = conditional_escape
    else:
        escape = lambda x: x
    
    node = getattr(value, 'dom_node', None)
    children = getattr(node, 'childNodes', ())
    parts = ( part for child in children
                   for part in node_parts(child, escape, include_tail=False) )
    result = ''.join(parts)
    return mark_safe(result)
format_ead_children.needs_autoescape = True

# Precompile XPath expressions for use in node_parts below.
_RENDER_DOUBLEQUOTE = etree.XPath('@render="doublequote"')
_RENDER_BOLD = etree.XPath('@render="bold"')
_RENDER_ITALIC = etree.XPath('@render="italic"')
_IS_EMPH = etree.XPath('self::emph')
_IS_TITLE = etree.XPath('self::title')

def node_parts(node, escape, include_tail):
    """Recursively convert a DOM node to HTML. This function is used
    internally by :func:`format_ead`. You probably want that function, not
    this one.
    
    This function returns an iterable over unicode chunks intended for easy
    joining by :func:`format_ead`.
    """

    # if current node contains text before the first node, pre-pend to list of parts
    text = node.text and escape(node.text)
        
    # if this node contains other nodes, start with a generator expression
    # to recurse into children, getting the node_parts for each.
    child_parts = ( part for child in node
                         for part in node_parts(child, escape, include_tail=True) )

    tail = include_tail and node.tail and escape(node.tail)
    
    # format the current node, and either wrap child parts in appropriate
    # fenceposts or return them directly.
    return _format_node(node, text, child_parts, tail)

def _format_node(node, text, contents, tail):
    # format a single node, wrapping any contents, and passing any 'tail' text content
    if _RENDER_DOUBLEQUOTE(node):
        return _wrap('"', text, contents, '"', tail)
    elif _RENDER_BOLD(node):
        return _wrap('<span class="ead-bold">', text, contents, '</span>', tail)
    elif _RENDER_ITALIC(node):
        return _wrap('<span class="ead-italic">', text, contents, '</span>', tail)
    elif _IS_EMPH(node):
        return _wrap('<em>', text, contents, '</em>', tail)
    elif _IS_TITLE(node):
        return _wrap('<span class="ead-title">', text, contents, '</span>', tail)
    else:
        return _wrap(None, text, contents, None, tail)

def _wrap(begin, text, parts, end, tail):
    """Wrap some iterable parts in beginning and ending fenceposts. Simply
    yields begin, then each part, then end."""
    if begin:
        yield begin
    if text:
        yield text

    for part in parts:
        yield part

    if end:
        yield end
    if tail:
        yield tail
