import os
from lxml.etree import XMLSyntaxError, Resolver, tostring
import re

from django.conf import settings
from django.http import HttpResponseRedirect

from eulcore.xmlmap.core import load_xmlobject_from_file, load_xmlobject_from_string
from findingaids.fa.models import FindingAid
from findingaids.fa.urls import EADID_URL_REGEX, TITLE_LETTERS

def check_ead(filename, dbpath, xml=None):
    """
    Sanity check an EAD file before it is loaded to the configured database.

    Checks the following:
     - DTD valid (file must include doctype declaration)
     - eadid matches expected pattern-- filename without .xml
     - check that eadid is unique within the database (only present once, in the file that will be updated)
     - additional checks done by :meth:`check_eadxml`

    :param filename: full path to the EAD file to be checked
    :param dbpath: full path within eXist where the document will be saved
    :returns: list of all errors found
    :rtype: list
    """
    errors = []
    if xml is not None:
        load_xml = load_xmlobject_from_string
        content = xml
    else:
        load_xml = load_xmlobject_from_file
        content = filename
    
    try:
        ead = load_xml(content, FindingAid, validate=True, resolver=EadDTDResolver())
    except XMLSyntaxError, e:
        # NOTE: we could report all syntax/validation errors if we validate with
        # a dtd object and access the error_log on the dtd object.
        # It's probably sufficient to report the first error and direct the user
        # to validate offline; possibly when we switch to an XSD schema this could
        # be revisited - load without validation, then validate and report all errors
        errors.append(e)       
        # if not dtd-valid, then appempt to load without validation to do additional checking
        try:
            ead = load_xml(content, FindingAid, validate=False, resolver=EadDTDResolver())
        except XMLSyntaxError, e:
            # if this fails, document is not well-formed xml
            # don't bother appending the syntax error, it will be the same one found above
            # can't do any further processing, so return
            return errors
    
    # eadid is expected to match filename without .xml extension
    expected_eadid = os.path.basename(filename).replace('.xml', '')
    if ead.eadid.value != expected_eadid :
        errors.append("eadid '%s' does not match expected value of '%s'" % (ead.eadid.value, expected_eadid))
    else:   # if eadid is acceptable, check for uniqueness in configured database
        fa = FindingAid.objects.filter(eadid=ead.eadid.value).only("document_name", "collection_name")
        if fa.count() > 1:
            errors.append("Database already contains %s instances of eadid '%s'! (%s)"
                    % (fa.count(), ead.eadid.value, ", ".join([f.document_name for f in fa])))
        elif fa.count() == 1:
            # some inconsistency in when /db is included on exist collection names
            path = fa[0].collection_name.replace('/db', '') + "/" + fa[0].document_name
            if path != dbpath:
                errors.append("Database contains eadid '%s' in a different document (%s)"
                    % (ead.eadid.value, fa[0].document_name))

    errors.extend(check_eadxml(ead))

    return errors

def check_eadxml(ead):
    """Sanity checks specific to the EAD xml, independent of file or eXist.

    Checks the following:
     - series and index ids are present
     - fields used for search/browse title match code expectations:
        - at most one top-level origination
        - no leading whitespace in list-title (origination or unittitle)
        - alphabetical first letter (for first-letter browse)
     - eadid matches site URL regex

    :param ead: :class:`~findingaids.fa.models.FindingAid` ead instance to be checked
    :returns: list of all errors found
    :rtype: list
    """
    # NOTE: throughout, be sure to use unicode instead of string
    errors = []

    # check that series ids are set
    if ead.dsc and ead.dsc.hasSeries():
        for series in ead.dsc.c:
            errors.extend(check_series_ids(series))

    # check that any index ids are set
    for index in ead.archdesc.index:
        if not index.id:
            errors.append("%(node)s id attribute is not set for %(label)s"
                % { 'node' : index.node.tag, 'label' : unicode(index.head) })

    # eadid matches appropriate site URL regex
    if not re.match('^%s$' % EADID_URL_REGEX, ead.eadid.value):   # entire eadid should match regex
        errors.append("eadid '%s' does not match site URL regular expression" \
                      % ead.eadid.value)

    # multiple tests to ensure xml used for search/browse list-title matches what code expects
    # -- since list title is pulled from multiple places, give enough context so it can be found & corrected
    list_title_path = "%s/%s" % (ead.list_title.node.getparent().tag, ead.list_title.node.tag)
    # - check for at most one top-level origination
    origination_count = ead.node.xpath('count(archdesc/did/origination)')
    if int(origination_count)  > 1:
        errors.append("Site expects only one archdesc/did/origination; found %d" \
                        % origination_count)

    # container list formatting (based on encoding practice) expects only 2 containers per did
    containers = ead.node.xpath('//did[count(container) > 2]')
    if len(containers):
        errors.append("Site expects maximum of 2 containers per did; found %d did(s) with more than 2" \
                        % len(containers))
        errors.append(['Line %d: %s' % (c.sourceline, tostring(c)) for c in containers])

    # - no leading whitespace in list title
    title_node = ead.node.xpath("%s/text()" % ead.list_title_xpath)    
    if hasattr(title_node[0], 'text'):
        title_text = title_node[0].text
    else:
        title_text = unicode(title_node)
    if re.match('\s+', title_text):
        # using node.text because unicode() normalizes, which obscures whitespace problems
        errors.append("Found leading whitespace in list title field (%s): '%s'" % \
                        (list_title_path, ead.list_title.node.text) )
        # report with enough context that they can find the appropriate element to fix
        
    # - first letter of title matches regex   -- only check if whitespace test fails
    elif not re.match(TITLE_LETTERS, ead.first_letter):
        errors.append("First letter ('%s') of list title field %s does not match browse letter URL regex '%s'" % \
                      (ead.first_letter, list_title_path, TITLE_LETTERS) )

    # leading whitespace in control access fields (if any)
    if ead.archdesc.controlaccess and ead.archdesc.controlaccess.controlaccess:
        for ca in ead.archdesc.controlaccess.controlaccess:
            for term in ca.terms:
                if re.match('\s+', term.value):
                    errors.append("Found leading whitespace in controlaccess term '%s' (%s)" \
                                 % (term.value, term.node.tag))
    return errors
   
def check_series_ids(series):
    """Recursive function to check that series and subseries ids are present.
    
    :param series: :class:`findingaids.fa.models.Series`
    :returns: list of errors, if any
    """
    errors = []
    if not series.id:
        errors.append("%(level)s %(node)s id attribute is not set for %(label)s"
                % { 'node' : series.node.tag, 'level' : series.level, 'label' : series.display_label() })
    if series.hasSubseries():
        for c in series.c:
            errors.extend(check_series_ids(c))
    return errors


def prep_ead(ead, filename):
    """Prepare EAD xml for publication.  Currently does the following:
    
     - sets the eadid and ids on any series, subseries, and index elements based
       on filename and series unitid or index number.
     - removes any leading whitespace from controlaccess terms

    :param ead: :class:`~findingaids.fa.models.FindingAid` ead instance to be prepared
    :param string: filename of the EAD file (used as base eadid)
    :rtype: :class:`~findingaids.fa.models.FindingAid`
    """

    # eadid should be document name without .xml extension
    ead.eadid.value = os.path.basename(filename).replace('.xml', '')
    # set series ids
    if ead.dsc and ead.dsc.hasSeries():
        for i, series in enumerate(ead.dsc.c):
            set_series_ids(series, ead.eadid.value, i)
    # set index ids 
    for i, index in enumerate(ead.archdesc.index):
        # generate index ids based on eadid and index number (starting at 1, not 0)
        index.id = "%s_index%s" % (ead.eadid.value, i+1)

    # remove any leading whitespace in list title fields
    # NOTE: only removing *leading* whitespace because these fields
    # can contain mixed content, and trailing whitespace here may be significant
    # - list title fields - origination nodes and unittitle
    for field in ead.node.xpath('archdesc/did/origination/node()|archdesc/did/unittitle'):
        if hasattr(field, 'text'):
            field.text = unicode(field.text).lstrip()
    # - controlaccess fields (if any)
    if ead.archdesc.controlaccess and ead.archdesc.controlaccess.controlaccess:
        for ca in ead.archdesc.controlaccess.controlaccess:
            for term in ca.terms:
                term.value = term.value.lstrip()            

    return ead

def set_series_ids(series, eadid, position):
    """Recursive function to set series and subseries ids.  Series id will be set
    to something like ''eadid_series1'', where series1 is a lower-case, spaceless
    version of the series unitid.  If no unitid is present, the second half of
    the series id will be set based on the series level (e.g., series, subseries)
    and its position in the list of series in the document.

    :param series: :class:`findingaids.fa.models.Series`
    :param eadid: eadid of the document this series belongs to
    :param position: numerical position in series-- used as fall-back to generate
            series id when series does not have a unitid
    :returns: list of errors, if any
    """
    if series.did.unitid:
        series.id = "%s_%s" % (eadid, series.did.unitid.replace(' ', '').lower())
    else:
        # fall-back id: generate from c-level (series, subseries) and position in the series
        series.id = "%s_%s%s" % (eadid, series.level.lower(), position + 1)
    if series.hasSubseries():
        for j, c in enumerate(series.c):
            set_series_ids(c, eadid, j)


class EadDTDResolver(Resolver):
    """Custom :class:`lxml.etree.Resolver` that loads the **ead.dtd** from a
    known location (packaged with the source code)."""
    def resolve(self, url, id, context):
        if url == 'ead.dtd' or url.split('/')[-1] == 'ead.dtd':
            # when loading a file, the 'url' gets set to the fullpath of that file plus ead.dtd
            # assuming that anything coming in as ead.dtd can use our local copy (no variant DTDs)
            filepath = os.path.join(settings.BASE_DIR, 'fa', 'fixtures', 'ead.dtd')
            return self.resolve_filename(filepath, context)
        else:
            return super(EadDTDResolver, self).resolve(url, id, context)


class HttpResponseSeeOther(HttpResponseRedirect):
    """Variant of Django's :class:`django.http.HttpResponseRedirect`.  Used to
    simplify redirecting with status code 303, since this type of redirect is
    used frequently in fa_admin.

    303 See Other - not a replacement for the requested content, but a different resource
    """
    status_code = 303   # See Other - not a replacement for the requested content, but a different resource
