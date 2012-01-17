import os
import logging
from lxml.etree import XMLSyntaxError, XPath, tostring
import re
from urllib2 import HTTPError

from django.conf import settings
from django.core.urlresolvers import reverse

from eulxml.xmlmap.core import load_xmlobject_from_file, load_xmlobject_from_string
from eulxml.xmlmap.eadmap import EAD_NAMESPACE
from pidservices.djangowrapper.shortcuts import DjangoPidmanRestClient
from pidservices.clients import is_ark, parse_ark

from findingaids.fa.models import FindingAid, ID_DELIMITER
from findingaids.fa.urls import EADID_URL_REGEX, TITLE_LETTERS

# pre-compile an xpath to easily get node names without EAD namespace
local_name = XPath('local-name()')

# init logger for this module
logger = logging.getLogger(__name__)

def check_ead(filename, dbpath, xml=None):
    """
    Sanity check an EAD file before it is loaded to the configured database.

    Checks the following:
     - EAD schema valid
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
        ead = load_xml(content, FindingAid)
    except XMLSyntaxError, e:
        # if this fails, document is not well-formed xml
        # can't do any further processing, so return
        errors.append(e)
        return errors

    # schema validation
    if not ead.schema_valid():
        # if not valid, report all schema validation errors
        # - simplify error message: report line & columen #s, and text of the error
        errors.extend('Line %d, column %d: %s' % (err.line, err.column, err.message)
                        for err in ead.validation_errors())
    
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
                % { 'node' : local_name(index.node), 'label' : unicode(index.head) })

    # eadid matches appropriate site URL regex
    if not re.match('^%s$' % EADID_URL_REGEX, ead.eadid.value):   # entire eadid should match regex
        errors.append("eadid '%s' does not match site URL regular expression" \
                      % ead.eadid.value)

    # multiple tests to ensure xml used for search/browse list-title matches what code expects
    # -- since list title is pulled from multiple places, give enough context so it can be found & corrected
    list_title_path = "%s/%s" % (local_name(ead.list_title.node.getparent()), 
                                 local_name(ead.list_title.node))
    # - check for at most one top-level origination
    origination_count = ead.node.xpath('count(e:archdesc/e:did/e:origination)',
                                       namespaces={'e': EAD_NAMESPACE})
    if int(origination_count)  > 1:
        errors.append("Site expects only one archdesc/did/origination; found %d" \
                        % origination_count)

    # container list formatting (based on encoding practice) expects only 2 containers per did
    # - dids with more than 2 containers
    containers = ead.node.xpath('//e:did[count(e:container) > 2]',
                                namespaces={'e': EAD_NAMESPACE})
    if len(containers):
        errors.append("Site expects maximum of 2 containers per did; found %d did(s) with more than 2" \
                        % len(containers))
        errors.append(['Line %d: %s' % (c.sourceline, tostring(c)) for c in containers])
    # - dids with only one container
    containers = ead.node.xpath('//e:did[count(e:container) = 1]',
                                namespaces={'e': EAD_NAMESPACE})
    if len(containers):
        errors.append("Site expects 2 containers per did; found %d did(s) with only 1" \
                        % len(containers))
        errors.append(['Line %d: %s' % (c.sourceline, tostring(c)) for c in containers])

    # - no leading whitespace in list title
    # FIXME: this first test may be redundant - possibly use only the first_letter check,
    # now that the first_letter xpath uses normalize-space
    title_node = ead.node.xpath("%s/text()" % ead.list_title_xpath,
                                namespaces={'e': EAD_NAMESPACE})
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
                # NOTE: using node text because term.value is now normalized
                if re.match('\s+', unicode(term.node.text)):
                    errors.append("Found leading whitespace in controlaccess term '%s' (%s)" \
                                 % (term.node.text, local_name(term.node)))

    # eadid url should contain resolvable ARK
    if ead.eadid.url is None or not is_ark(ead.eadid.url):
        errors.append("eadid url is either not set or not an ARK. " +
            "To correct, run the prep process again.")

    # eadid identifier should contain short-form ARK
    if ead.eadid.identifier is None or not is_ark(ead.eadid.identifier):
        errors.append("eadid identifier is either not set or not an ARK" +
            "To correct, run the prep process again.")

    # short- and long-form ARKs should match each other
    if ead.eadid.url is not None and ead.eadid.identifier is not None and \
        not ead.eadid.url.endswith(ead.eadid.identifier):
        errors.append("eadid url and identifier do not match: url '%s' should end with identifier '%s'" \
                     % (ead.eadid.url, ead.eadid.identifier))


    return errors
   
def check_series_ids(series):
    """Recursive function to check that series and subseries ids are present.
    
    :param series: :class:`findingaids.fa.models.Series`
    :returns: list of errors, if any
    """
    errors = []
    if not series.id:
        errors.append("%(level)s %(node)s id attribute is not set for %(label)s"
                % { 'node' : local_name(series.node),
                    'level' : series.level,
                    'label' : series.display_label() })
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
        index.id = "%s%sindex%s" % (ead.eadid.value, ID_DELIMITER, i+1)

    # remove any leading whitespace in list title fields
    # NOTE: only removing *leading* whitespace because these fields
    # can contain mixed content, and trailing whitespace here may be significant
    # - list title fields - origination nodes and unittitle
    for field in ead.node.xpath('e:archdesc/e:did/e:origination/node()|e:archdesc/e:did/e:unittitle',
                                namespaces={'e': EAD_NAMESPACE}):
        # the text of an lxml node is the text content *before* any child elements
        # in some finding aids, this could be blank, e.g.
        # <unittitle><title>Pitts v. Freeman</title> case files</unittitle>
        # note that this clean does NOT handle leading whitespace in a leading child element.
        if hasattr(field, 'text') and field.text is not None:
            field.text = unicode(field.text).lstrip()
    # - controlaccess fields (if any)
    if ead.archdesc.controlaccess and ead.archdesc.controlaccess.controlaccess:
        for ca in ead.archdesc.controlaccess.controlaccess:
            for term in ca.terms:
                # Using node.text here because term.value is normalized
                # NOT forcing normalization on control access terms because
                # XML editor line-wrap settings would force
                # re-running the prep step every time a document is edited.
                if term.node.text:
                    term.value = term.node.text.lstrip()

    # check that ARK is set correctly (both long and short-form)
    # - if eadid url is not set or is not an ark, generate an ark
    if ead.eadid.url is None or not is_ark(ead.eadid.url):
        ead.eadid.url = generate_ark(ead)
    # - if eadid identifier is not set or not an ark, calculate short-form ark from eadid url
    if ead.eadid.identifier is None or not is_ark(ead.eadid.identifier):
        ark_parts = parse_ark(ead.eadid.url)
        ead.eadid.identifier = 'ark:/%(naan)s/%(noid)s' % ark_parts
    return ead

def generate_ark(ead):
    '''Generate an ARK for the specified EAD document.  ARK will be created
    with a default target of the url for the main page of the specified EAD
    document in this site.

    :param ead: :class:`findingaids.fa.models.FindingAid` instance
    :returns: resolvable URL for generated ARK on success
    '''
    # catch init error and report simplified error to user
    try:
        pidclient = DjangoPidmanRestClient()
    except RuntimeError:
        raise Exception("Error initializing PID Manager client; please check site configuration.")

    # check that domain is set
    if not hasattr(settings, 'PIDMAN_DOMAIN'):
        raise Exception("Unable to generate ARK: PID manager domain is not configured.")

    # generate absolute url for ARK target
    ead_url = settings.SITE_BASE_URL.rstrip('/') + reverse('fa:findingaid',
                                               kwargs={'id' : ead.eadid.value })

    try:
        # search for an existing ARK first, in case one was already created for this ead
        # limit search by the configured domain; look for an ARK with the expected target url
        found = pidclient.search_pids(type='ark', target=ead_url,
                                            domain_uri=settings.PIDMAN_DOMAIN)
        # at least one match
        if found and found['results_count']:
            if found['results_count'] > 1:
                # uh-oh - this shouldn't happen; warn the user
                logger.warning("Found %d ARKs when searching for an existing ARK for %s" \
                    % (found['results_count'], ead.eadid.value))

            # use existing pid
            pid = found['results'][0]
            # find the unqualified target and get the access uri - primary resolvable ark url
            for t in pid['targets']:
                if 'qualifier' not in t or not t['qualifier']:
                    ark_url = t['access_uri']

            logger.info("Using existing ARK %s for %s" % (ark_url, ead.eadid.value))

            # what if no default target is not found? (unlikely but possible...)
            return ark_url

        # if no matches found, create a new ark
        return pidclient.create_ark(settings.PIDMAN_DOMAIN, ead_url,
                                   name=unicode(ead.unittitle))

    # any error in the pidclient is raised as an HTTPError
    except HTTPError as err:
        raise Exception('Error generating ARK: %s' % err)



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
        series.id = "%s%s%s" % (eadid, ID_DELIMITER, series.did.unitid.value.replace(' ', '').lower())
    else:
        # fall-back id: generate from c-level (series, subseries) and position in the series
        series.id = "%s%s%s%s" % (eadid, ID_DELIMITER, series.level.lower(), position + 1)
    if series.hasSubseries():
        for j, c in enumerate(series.c):
            set_series_ids(c, eadid, j)
