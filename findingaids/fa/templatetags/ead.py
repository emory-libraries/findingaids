"""
Custom filters for processing EAD structured fields to HTML.
"""

from lxml import etree

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from eulcore.xmlmap import XmlObject

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
        parts = node_parts(value.dom_node, escape)
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
                   for part in node_parts(child, escape) )
    result = ''.join(parts)
    return mark_safe(result)
format_ead_children.needs_autoescape = True

# Precompile XPath expressions for use in node_parts below.
_RENDER_DOUBLEQUOTE = etree.XPath('@render="doublequote"')
_RENDER_BOLD = etree.XPath('@render="bold"')
_RENDER_ITALIC = etree.XPath('@render="italic"')
_IS_EMPH = etree.XPath('self::emph')
_IS_TITLE = etree.XPath('self::title')

def node_parts(node, escape):
    """Recursively convert a DOM node to HTML. This function is used
    internally by :func:`format_ead`. You probably that function, not this
    one.
    
    This function returns an iterable over unicode chunks intended for easy
    joining by :func:`format_ead`.
    """

    if len(node):
        # if this node contains other nodes, start with a generator expression
        #to recurse into children, getting the node_parts for each.
        child_parts = [ part for child in node
                             for part in node_parts(child, escape)]      
        
        # if current node contains text before the first node, pre-pend to list of parts
        if node.text:
            child_parts.insert(0, escape(node.text))
            
        # format the current node, and either wrap child parts in appropriate
        # fenceposts or return them directly.
        return _format_node(node, child_parts)        
    else:
        # element with no child nodes - format and return
        return _format_node(node, escape(node.text))

def _format_node(node, contents):
    # format a single node, wrapping any contents, and passing any 'tail' text content
    if _RENDER_DOUBLEQUOTE(node):
        return _wrap('"', contents, '"', node.tail)
    elif _RENDER_BOLD(node):
        return _wrap('<span class="ead-bold">', contents, '</span>', node.tail)
    elif _RENDER_ITALIC(node):
        return _wrap('<span class="ead-italic">', contents, '</span>', node.tail)
    elif _IS_EMPH(node):
        return _wrap('<em>', contents, '</em>', node.tail)
    elif _IS_TITLE(node):
        return _wrap('<span class="ead-title">', contents, '</span>', node.tail)
    else:
        return contents

def _wrap(begin, parts, end, tail=None):
    """Wrap some iterable parts in beginning and ending fenceposts. Simply
    yields begin, then each part, then end."""
    yield begin
    for part in parts:
        yield part
    yield end
    if tail is not None:
        yield tail
