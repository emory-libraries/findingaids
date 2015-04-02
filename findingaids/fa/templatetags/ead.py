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
from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe

from eulxml.xmlmap.eadmap import EAD_NAMESPACE
from findingaids.fa.models import title_rdf_identifier

__all__ = ['format_ead', 'format_ead_rdfa', 'series_section_rdfa']

register = template.Library()

XLINK_NAMESPACE = 'http://www.w3.org/1999/xlink'
EXIST_NAMESPACE = 'http://exist.sourceforge.net/NS/exist'

# namespace info to pass to xpath to allow referencing ead ns
eadns = {'namespaces': {'e': EAD_NAMESPACE}}

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


def format_extref(node,):
    'convert an extref node to an html link'
    url = node.get('{%s}href' % XLINK_NAMESPACE)
    href = ' href="%s"' % url if url is not None else ''
    rel = ''
    # special case: links in separated/related material should be relatedLink
    if node.xpath('ancestor::e:separatedmaterial or ancestor::e:relatedmaterial',
                  **eadns):
        rel = ' property="schema:relatedLink" '

    return ('<a%s%s>' % (rel, href), '</a>')


def format_date(node, default_rel):
    'display a date node with semantic information, if available'
    normal = node.get('normal', None)
    # default to dc:date property as a generic date
    date_type = node.get('type', 'dc:date')
    start, end = '', ''
    # display if we have a normalized date
    if normal is not None:
        start = '<span property="%s" content="%s">' % (date_type, normal)
        end = '</span>'
    return (start, end)


def format_title(node, default_rel):
    'display a title node as semantic information'
    title_type = node.get('type', None)
    title_source = node.get('source', None)
    title_authfileno = node.get('authfilenumber', None)
    # lower-case title source for consistency of checking (isbn/issn/oclc)
    if title_source is not None:
        title_source = title_source.strip().lower()
    # strip space from authfileno, to avoid any issues due to human error
    if title_authfileno is not None:
        title_authfileno = title_authfileno.strip()

    start, end = '', ''

    # special case we can't do anything with
    # if a title is inside the bioghist, we can assume it was created by the
    # originator, *however* there is no inverse relationship to specify
    # a title was created by a person.  We also can't assume
    # any relation to the collection.  So, skip these titles for now.
    if node.xpath('ancestor::e:bioghist', **eadns):
        return (start, end)
    # similar special case: if a title is inside a series scopecontent note
    # which is related to a series unititle person (see note on series_section_rdfa),
    # do not generate any RDFa for that title
    if node.xpath('ancestor::e:scopecontent/preceding-sibling::e:did/e:unittitle[e:corpname or e:persname]',
                  **eadns):
        return (start, end)

    # for now, ignore titles in correspondence series
    # (getting associated with the person inappropriately)
    if default_rel == 'schema:knows arch:correspondedWith':
        return start, end

    # if isbn # or issn is available, include it
    meta_tags = ''
    if title_source in ['isbn', 'issn'] and title_authfileno is not None:
        meta_tags += '<meta property="schema:%s" content="%s"/>' % \
            (title_source, title_authfileno)
    # title attribute carries genre information
    if title_type is not None:
        meta_tags += '<meta property="schema:genre" content="%s"/>' % title_type

    # generate URI/URN for item when possible
    # TODO: abstract into reusable function
    resource_id = None
    if title_authfileno is not None:
        resource_id = title_rdf_identifier(title_source, title_authfileno)

    # resource attribute for inclusion
    resource = ' resource="%s"' % resource_id if resource_id else ''

    # if title is inside the scopecontent, it needs to be wrapped as a document
    # just use the generic "mentions" relation
    if node.xpath('ancestor::e:scopecontent', **eadns):
        # mark as a generic document or periodical and include whatever meta tags are available
        itemtype = 'bibo:Periodical' if title_source == 'issn' else 'bibo:Document'
        start = '<span rel="schema:mentions" typeof="%s"%s><span property="dc:title">' \
                 % (itemtype, resource)
        end = '</span>%s</span>' % meta_tags

    # if default rel is set to mention, assume we are patching in extra titles
    # after file item unittitle context
    elif default_rel == 'schema:mentions':
        if title_source == 'issn':
            itemtype = 'bibo:Periodical'
        elif title_source in ['isbn', 'oclc']:
            itemtype = 'bibo:Document'
        else:
            # technically we should be checking if this is a printed materials series...
            itemtype = 'bibo:Manuscript'

        # if this title has a type but no authfilenumber and there is a
        # sibling title with an id, relate them
        if title_type is not None and title_authfileno is None \
                      and node.xpath('parent::e:unittitle/e:title[@authfilenumber]',
                                     **eadns):
            rel_id = None
            rel_authfileno = node.xpath('normalize-space(parent::e:unittitle/e:title/@authfilenumber)',
                                        **eadns).strip()
            rel_source = node.xpath('normalize-space(parent::e:unittitle/e:title/@source)',
                                    **eadns).lower()

            rel_id = title_rdf_identifier(rel_source, rel_authfileno)

            if rel_id is not None:
                meta_tags += '<span property="dcterms:isPartOf" resource="%s"/>' % rel_id

        start = '<span rel="schema:mentions" typeof="%s"%s><span property="dc:title">' \
                 % (itemtype, resource)
        end = '</span>%s</span>' % meta_tags

    # Otherwise, only add semantic information if there is a title type OR
    # if title occurs in a file-level unittitle.
    # (in that case, we assume it is title of the item in the container)
    elif node.xpath('parent::e:unittitle and ancestor::e:*[@level="file"]',
                  **eadns) or title_type is not None:
        start, end = '<span property="dc:title">', '</span>%s' % meta_tags
        # include meta tags after the title, since it should be in the
        # context of the item, which is the whole unitittle

        # check for special case: multiple titles with an author
        # (persname tagged with a role, i.e. this is a Belfast Group sheet),
        multiple_with_author = title_type is None \
                and node.xpath('count(parent::e:unittitle/e:title)',
                               **eadns) > 1 \
                and node.xpath('preceding-sibling::e:persname[@role]',
                               **eadns)

        # special case: no good way to relate more than two titles in a unittitle,
        # so just skip them when generating rdfa
        if node.xpath('count(preceding-sibling::e:title)', **eadns) >= 2 \
          and not multiple_with_author:
            start, end = '', ''

        # if ISSN with preceding title, assume article in a periodical
        elif title_source == 'issn' and \
            node.xpath('count(preceding-sibling::e:title)', **eadns) == 1:
            print node.xpath('text()')
            print '*** ISSN, preceding title count is 1'
            # adapted from schema.org article example: http://schema.org/Article
            start = '<span property="dcterms:isPartOf" typeof="bibo:Periodical"%s><span property="dc:title">' % resource
            # include any meta tags (genre, issn) inside the periodical entity
            end = '</span>%s</span>' % meta_tags

        # otherwise, if current title has an id or no type and follows a title with a type,
        # assume generic part/whole relationship
        elif (title_authfileno is not None or title_type is None) and \
            node.xpath('count(./preceding-sibling::e:title[@type])', **eadns) == 1:
            print node.xpath('text()')
            print '*** preceding title count is ', node.xpath('count(./preceding-sibling::e:title[@type])', **eadns)
            start = '<span property="dcterms:isPartOf" typeof="bibo:Document"%s><span property="dc:title">' % resource
            # include any meta tags (e.g. isbn) inside the document entity
            end = '</span>%s</span>' % meta_tags

        # if no type and there are multiple titles, AND there is a persname
        # tagged with a role (i.e. this is a Belfast Group sheet),
        # then use RDFa list notation to generate a sequence
        elif title_type is None and node.xpath('count(parent::e:unittitle/e:title)',
                                               **eadns) > 1 \
                                and node.xpath('preceding-sibling::e:persname[@role]',
                                               **eadns):
            start = '<span inlist="inlist" property="dc:title">'

    return (start, end)


def format_occupation(node, default_rel):
    'display an occupation node with semantic information'
    return ('<span property="schema:jobTitle">', '</span>')


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
# tags that are not names, but should only be styled for rdfa
semantic_tags = {
    '{%s}date' % EAD_NAMESPACE: format_date,
    '{%s}title' % EAD_NAMESPACE: format_title,
    '{%s}occupation' % EAD_NAMESPACE: format_occupation,
}

# default roles for names in the bioghist, based on type of name
# and type of origination name
default_bioghist_roles = {
    'person': {
        'schema:Person': 'schema:knows',
        'schema:Organization': 'schema:affiliation',
    },
    'org': {
        'schema:Person': 'schema:affiliation',
        'schema:Organization': 'schema:affiliation',
    }
}


def format_nametag(node, default_role=None):
    '''Convert a supported name tag into corresponding RDFa.
    '''
    rdftype = name_tags.get(node.tag, None)

    # if not a supported type, don't tag at all
    if rdftype is None:
        return ('', '')

    about = ''
    uri = None
    if node.get('authfilenumber') is not None:
        # get authfilenumber attribute, stripping any whitespace to avoid
        # generating invalid URIs
        authnum = node.get('authfilenumber').strip()
        if node.get('source') == 'viaf':
            uri = 'http://viaf.org/viaf/%s' % authnum
        elif node.get('source') == 'geonames':
            uri = 'http://sws.geonames.org/%s/' % authnum
        elif node.get('source') == 'dbpedia':
            # escaping here because in some cases,
            # dbpedia identifiers may include & or similar (!)
            uri = 'http://dbpedia.org/resource/%s' % escape(authnum)

        if uri is not None:
            about = ' about="%s"' % uri

    start = '<span%s typeof="%s"><span property="schema:name">' % \
            (about, rdftype)
    end = '</span></span>'

    # NOTE: *preliminary* role  / relation to context
    rel = default_role
    if rel is None:
        # NOTE: *preliminary* role  / relation to context
        if node.get('role') is not None:
            rel = node.get('role')

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

        # fallback roles, set based on content
        if rel is None:

            # if name is in the bioghist, infer relation based on origination type
            if node.xpath('ancestor::e:bioghist', **eadns):

                # special case: don't assume anything for geogname with no role
                if rdftype == 'schema:Place':
                    return ('', '')

                origination = node.xpath('ancestor::e:archdesc/e:did/e:origination/*',
                                         **eadns)
                if origination:
                    orig_type = None
                    orig = origination[0]
                    if orig.tag.endswith('persname'):
                        orig_type = 'person'
                    elif orig.tag.endswith('corpname'):
                        orig_type = 'org'

                    if orig_type is not None:
                        # determine default role based on origination name and
                        # type of current name
                        rel = default_bioghist_roles[orig_type].get(rdftype, None)

        # if nothing else, the document obviously mentions this entity
        if rel is None:
            # *unless* we are in in a file-level unitittle that is elsewhere
            # assumed to be "about" a title, which cannot *mention* a person
            if node.xpath('ancestor::e:*[@level="file"] and parent::e:unittitle[e:title[@type] or e:title[@source and @authfilenumber]]',
                         **eadns):
                rel = None
            else:
                rel = 'schema:mentions'

    if rel is not None:
        start = '<span rel="%s">%s' % (rel, start)
        end += '</span>'

    return (start, end)


@register.filter(needs_autoescape=True)
def format_ead(value, autoescape=None, rdfa=False, default_rel=None):
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
        result = format_ead_node(value.node, esc, rdfa, default_rel)
    else:
        result = ''

    return mark_safe(result)


@register.filter(needs_autoescape=True)
def format_ead_rdfa(value, default_rel=None, autoescape=None):
    '''Custom filter to convert EAD to HTML, with support for converting
    name tags such as persname, corpname, and geogname to RDFa.

    :param default_rel: relationship to use for all entities
       found under this node
    '''
    return format_ead(value, autoescape, rdfa=True, default_rel=default_rel)


def format_ead_node(node, escape, rdfa=False, default_rel=None):
    '''Recursive method to generate HTML with the text and any
    formatting for the contents of an EAD node.

    :param node: lxml element or node to be converted from EAD to HTML
    :param escape: template escape method to be used on node text content
    :returns: string with the HTML output
    '''
    # find any start/end tags for the current element

    # check for supported render attributes
    rend = node.get('render', None)

    rdfa_start, rdfa_end = '', ''

    # convert names to semantic web / rdfa if requested
    if rdfa and node.tag in name_tags.keys():
        rdfa_start, rdfa_end = format_nametag(node, default_rel)

    elif rdfa and node.tag in semantic_tags.keys():
        rdfa_start, rdfa_end = semantic_tags[node.tag](node, default_rel)

    # convert display/formatting
    # NOTE: a few semantic tags also have formatting conversion

    start, end = '', ''
    if rend is not None and rend in rend_attributes.keys():
        s, e = rend_attributes[rend]
        start += s
        end = e + end

    # simple tags that can be converted to html markup
    elif node.tag in simple_tags.keys():
        start, end = simple_tags[node.tag]

    # more complex tags
    elif node.tag in other_tags.keys():
        start, end = other_tags[node.tag](node)

    # unsupported tags that do not get converted
    else:
        start, end = '', ''

    start += rdfa_start
    end = rdfa_end + end

    # list of text contents to be compiled
    contents = [start]  # start tag
    # include any text directly in this node, before the first child
    if node.text is not None:
        contents.append(escape(node.text))

    # format any child nodes and add to the list of text
    contents.extend([format_ead_node(el, escape=escape, rdfa=rdfa,
                                     default_rel=default_rel)
                     for el in node.iterchildren()])

    # end tag for this node + any tail text
    contents.extend([end, escape(node.tail or '')])

    return ''.join(contents)

EAD_SCOPECONTENT = '{%s}scopecontent' % EAD_NAMESPACE
EAD_BIOGHIST = '{%s}bioghist' % EAD_NAMESPACE


@register.assignment_tag(takes_context=True)
def series_section_rdfa(context, series, section):
    # determine rdf wrapping info for a series info section

    # NOTE: technically anything in the scopecontent not should
    # relate to the *collection* and not to any individual.
    # However, initial RDFa implementation for Belfast project
    # assumed a relationship between series scopecontent notes and the
    # origination entity or a tagged name in the series title.
    # This does not generalize well OR work with titles (no way to relate
    # an author to a title); for now only expose RDFa for series
    # content when there is a series unittitle name.
    name = series.unittitle_name

    type = None
    if name is not None:
        if name.is_personal_name:
            type = 'schema:Person'
        elif name.is_corporate_name:
            type = 'schema:Organization'
        elif name.is_geographic_name:
            type = 'schema:Place'

    rdfa = False
    default_rel = None

    # sections at series level we want to treat as *about*
    # the name
    if name is not None and type is not None and name.uri is not None \
       and section.node.tag in [EAD_SCOPECONTENT, EAD_BIOGHIST]:
        rdfa = True

    # is section is scopecontent or bioghist, then assume it is about
    # closest named person/organization

    if rdfa and 'correspondence' in unicode(series.did.unittitle).lower():
        default_rel = 'schema:knows arch:correspondedWith'

    # if there is semantic information to display, the web page
    # is *about* the person/org; use

    if rdfa:
        start = '''<div rel="schema:about">
            <div typeof="%s" about="%s">
        ''' % (type, name.uri)
        end = '</div></div>'

        context['use_rdfa'] = True
    else:
        start = '<div>'
        end = '</div>'

    context.update({'use_rdfa': rdfa, 'default_rel': default_rel})

    return {'start': mark_safe(start), 'end': mark_safe(end)}
