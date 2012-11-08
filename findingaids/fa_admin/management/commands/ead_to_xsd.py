# file findingaids/fa_admin/management/commands/ead_to_xsd.py
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

import glob
from lxml import etree
from optparse import make_option
from os import path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    """Convert DTD-based EAD to XSD schema-based EAD.

If filenames are specified as arguments, only those files will be converted.
Files should be specified by basename only (assumed to be in the configured
EAD source directory). Otherwise, all .xml files in the configured EAD source
directory will be converted."""
    help = __doc__

    args = '[<filename filename ... >]'

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n',
            dest='dryrun',
            action='store_true',
            help='''Report on what would be done, but don't make any actual changes'''),
        )

    # canonical location of the EAD XSD schema
    schema_url = 'http://www.loc.gov/ead/ead.xsd'
    # parse and load the schema for validating converted documents
    eadschema = etree.XMLSchema(etree.parse(schema_url))
    # load XSLT for conversion
    dtd2schema = etree.XSLT(etree.parse(path.join(path.dirname(path.abspath(__file__)),
                            'dtd2schema.xsl')))
    # XML serialization options
    serialization_opts = {
        'encoding': 'UTF-8',
        'xml_declaration': True,
        'pretty_print': True
    }

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1
        v_all = 2
        
        # check for required settings
        if not hasattr(settings, 'FINDINGAID_EAD_SOURCE') or not settings.FINDINGAID_EAD_SOURCE:
            raise CommandError("FINDINGAID_EAD_SOURCE setting is missing")
            return

        if verbosity == v_all:
            print "Converting documents from configured EAD source directory: %s" \
                    % settings.FINDINGAID_EAD_SOURCE
            if options['dryrun']:
                print "Running in dry-run mode; no changes will be made"

        updated = 0
        unchanged = 0
        errored = 0

        if len(args):
            files = [path.join(settings.FINDINGAID_EAD_SOURCE, name) for name in args]
        else:
            files = glob.iglob(path.join(settings.FINDINGAID_EAD_SOURCE, '*.xml'))


        schemaLocation = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"

        for file in files:
            base_filename = path.basename(file)
            try:       
                # load file as xml
                doc = etree.parse(file)
                # check for schema definition in the file
                schema_loc = doc.getroot().get(schemaLocation)
                if schema_loc and self.schema_url in schema_loc:
                    if verbosity > v_normal:
                        print "%s has already been converted" % base_filename
                    # don't re-process files that have already been converted
                    unchanged += 1
                    continue
                    
                # run xslt
                result = self.dtd2schema(doc)
                # clean up details not handled by the XSLT conversion                
                #  @normal on <unitdate> and <date>: constrained to date and date range subset of ISO 8601
                #  @repositorycode: constrained to ISO 15511 (ISIL)
                #  @mainagencycode: same as @repositorycode
                #  @langcode: constrained to ISO 639-2 alpha-3 code list
                #  @scriptcode: constrained to ISO 15924 code list
                for scriptcode in result.xpath('//@scriptcode'):
                    # case is significant; first letter should be capitalized
                    # current documents all have lower case 'latn', should be 'Latn'
                    scriptcode.getparent().set('scriptcode', scriptcode.title())
                # @countrycode: constrained to ISO 3166-1 alpha-2 code list
                for countrycode in result.xpath('//@countrycode'):
                    # case is significant, must be uppercase
                    # current documents all have lower case 'us' for countrycode, should be 'US'
                    countrycode.getparent().set('countrycode', countrycode.upper())

                # validate against XSD schema
                valid = self.eadschema.validate(result)
                if not valid:
                    errored += 1
                    if verbosity >= v_normal:
                        print "Error: converted document for %s is not schema valid" % base_filename
                    if verbosity > v_normal:
                        print "Validation errors:"
                        for err in self.eadschema.error_log:
                            print '  ', err.message
                # save if valid and not unchanged and not dry-run
                else:
                    # converted document is schema valid
                    updated += 1
                    if verbosity > v_normal:
                        # dry-run mode - if verbose, display
                        print "Updating %s %s" % (base_filename,
                                    '(simulated)' if options['dryrun'] else '')
                    if not options['dryrun']:
                        # not in dry-run mode - actually update the file
                        with open(file, 'w') as f:
                            f.write(etree.tostring(result,  **self.serialization_opts))
            except etree.XMLSyntaxError, e:
                # xml is not well-formed - couldn't even be loaded
                if verbosity >= v_normal:
                    print "Error: failed to load %s (document not well-formed XML?)" \
                                % base_filename

                errored += 1

        # summarize what was done
        if verbosity >= v_normal:
            print '-------------------------'
        print "%d document%s updated" % (updated, 's' if updated != 1 else '')
        print "%d document%s unchanged" % (unchanged, 's' if unchanged != 1 else '')
        print "%d document%s with errors" % (errored, 's' if errored != 1 else '')
            
