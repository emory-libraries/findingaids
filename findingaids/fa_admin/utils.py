import os
from lxml.etree import XMLSyntaxError, Resolver
from django.conf import settings

from eulcore.xmlmap.core import load_xmlobject_from_file, load_xmlobject_from_string
from findingaids.fa.models import FindingAid

def check_ead(filename, dbpath, xml=None):
    """
    Sanity check an EAD file before it is loaded to the configured database.

    Checks the following:
     - DTD valid (file must include doctype declaration)
     - eadid matches expected pattern (filename without .xml)
     - check that eadid is unique within the database (only present once, in the file that will be updated)
     - series and index ids are present     

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
    if ead.eadid != expected_eadid :
        errors.append("eadid '%s' does not match expected value of '%s'" % (ead.eadid, expected_eadid))
    else:   # if eadid is acceptable, check for uniqueness in configured database
        fa = FindingAid.objects.filter(eadid=ead.eadid).only("document_name", "collection_name")
        if fa.count() > 1:
            errors.append("Database already contains %s instances of eadid '%s'! (%s)"
                    % (fa.count(), ead.eadid, ", ".join([f.document_name for f in fa])))
        elif fa.count() == 1:
            # some inconsistency in when /db is included on exist collection names
            path = fa[0].collection_name.replace('/db', '') + "/" + fa[0].document_name
            if path != dbpath:
                errors.append("Database contains eadid '%s' in a different document (%s)"
                    % (ead.eadid, fa[0].document_name))            

    errors.extend(check_eadxml(ead))

    return errors

def check_eadxml(ead):
    """Sanity checks specific to the EAD xml, independent of file or eXist.
    Currently checks that expected ids are set (series, subseries, index).

    :param ead: :class:`~findingaids.fa.models.FindingAid` ead instance to be checked
    :returns: list of all errors found
    :rtype: list
    """
    errors = []

    # check that series ids are set
    if ead.dsc and ead.dsc.hasSeries():
        for series in ead.dsc.c:
            errors.extend(check_series_ids(series))

    # check that any index ids are set
    for index in ead.archdesc.index:
        if not index.id:
            errors.append("%(node)s id attribute is not set for %(label)s"
                % { 'node' : index.node.tag, 'label' : index.head })
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


def clean_ead(ead, filename):
    """Clean up EAD xml so it can be published. Sets the eadid and
    ids on any series, subseries, and index elements based on filename and series
    unitid or index number.

    :param ead: :class:`~findingaids.fa.models.FindingAid` ead instance to be cleaned
    :param string: filename of the EAD file (used as base eadid)
    :rtype: :class:`~findingaids.fa.models.FindingAid`
    """

    # eadid should be document name without .xml extension
    ead.eadid = os.path.basename(filename).replace('.xml', '')
    # set series ids
    if ead.dsc and ead.dsc.hasSeries():
        for i, series in enumerate(ead.dsc.c):
            set_series_ids(series, ead.eadid, i)
    # set index ids 
    for i, index in enumerate(ead.archdesc.index):
        # generate index ids based on eadid and index number (starting at 1, not 0)
        index.id = "%s_index%s" % (ead.eadid, i+1)

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

    