"""
Custom filters for processing EAD structured fields to HTML.
"""

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from Ft.Xml.XPath import Compile
from eulcore.xmlmap import XmlObject

__all__ = [ 'format_ead' ]

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


# Precompile XPath expressions for use in node_parts below.
_RENDER_DOUBLEQUOTE = Compile('@render="doublequote"')
_RENDER_BOLD = Compile('@render="bold"')
_RENDER_ITALIC = Compile('@render="italic"')
_IS_EMPH = Compile('self::emph')
_IS_TITLE = Compile('self::title')

def node_parts(node, escape):
    """Recursively convert a DOM node to HTML. This function is used
    internally by :func:`format_ead`. You probably that function, not this
    one.
    
    This function returns an iterable over unicode chunks intended for easy
    joining by :func:`format_ead`.
    """

    if node.nodeValue is not None:
        # A text node yields a single unicode chunk containing its
        # escaped contents.
        return [ escape(node.nodeValue) ]

    elif hasattr(node, 'childNodes'):
        # Element nodes yield their children, sometimes wrapped by start and
        # end tags. Start with a generator expression to recurse into children,
        # getting the node_parts for each.
        child_parts = ( part for child in node.childNodes
                             for part in node_parts(child, escape) )

        # And then depending on the details of the *current* node, either
        # wrap those child parts in appropriate fenceposts or return them
        # directly.
        if node.xpath(_RENDER_DOUBLEQUOTE):
            return _wrap('"', child_parts, '"')
        elif node.xpath(_RENDER_BOLD):
            return _wrap('<span class="ead-bold">', child_parts, '</span>')
        elif node.xpath(_RENDER_ITALIC):
            return _wrap('<span class="ead-italic">', child_parts, '</span>')
        elif node.xpath(_IS_EMPH):
            return _wrap('<em>', child_parts, '</em>')
        elif node.xpath(_IS_TITLE):
            return _wrap('<span class="ead-title">', child_parts, '</span>')
        else:
            return child_parts

    else:
        # Something else? Not sure what might fall into this category. Yield
        # nothing (effectively dropping the node) for now.
        return []


def _wrap(begin, parts, end):
    """Wrap some iterable parts in beginning and ending fenceposts. Simply
    yields begin, then each part, then end."""
    yield begin
    for part in parts:
        yield part
    yield end
