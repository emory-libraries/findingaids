# file findingaids/fa_admin/management/commands/itemid_to_dao.py
#
#   Copyright 2014 Emory University Library
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
import httplib2
from lxml.etree import XMLSyntaxError, cleanup_namespaces
from optparse import make_option
import os
import re
import sunburnt
from urlparse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from eulxml.xmlmap import eadmap
from eulxml.xmlmap.core import load_xmlobject_from_file

from findingaids.fa.models import FindingAid, Archive
from findingaids.fa_admin.svn import svn_client

class Command(BaseCommand):
    """Replace container-level item digital item ids with dao tags.

Looks through the container level item description of EAD xml files
to identify filename references in the unitid, look up those identifiers
in the Keep, and replace the note with one or more <dao> tags using the
ARK url for the identified item.

If filenames are specified as arguments, only those files will be prepared.
Files should be specified by full path. Otherwise, all .xml files in each of
the defined Archives will be prepared."""
    help = __doc__

    args = '[<filename filename ... >]'

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n',
            dest='dryrun',
            action='store_true',
            default=False,
            help='''Report on what would be done, but don't make any actual changes'''),
        make_option('--commit', '-c',
            dest='commit',
            action='store_true',
            default=False,
            help='''Commit changes to subversion after processing is finished'''),
    )


    # django default verbosity level options --  1 = normal, 0 = minimal, 2 = all
    v_normal = 1

    # TODO: report mode that will flag digitized notes where id isn't recognized
    # - include [digitized] with no id here
    # normal operation: error report if ids couldn't be pulled or processed (e.g. out of order range)

    # regex for recognizing digitized content
    digitized_ids = re.compile(ur'\[digitized;?( (Emory|filename)?:?\s*(?P<ids>[0-9a-z-,; ]+)\s*)?\]?\s*$',
                               re.IGNORECASE)


    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', self.v_normal))
        svn_commit = options.get('commit', False)
        dry_run = options.get('dryrun', False)

        # check for required settings
        if not hasattr(settings, 'KEEP_SOLR_SERVER_URL') or not settings.KEEP_SOLR_SERVER_URL:
            raise CommandError("KEEP_SOLR_SERVER_URL setting is required for this script")
            return

        solr = solr_interface()

        if verbosity > self.v_normal:
            print "Preparing documents from all defined Archives"
            if dry_run:
                print "Running in dry-run mode; no changes will be made"

        updated = 0
        unchanged = 0
        errored = 0

        if len(args):
            files = args
        else:
            # Note: copied from prep_ead manage command; move somewhere common?
            files = set()
            svn = svn_client()
            for archive in Archive.objects.all():
                # update to make sure we have latest version of everything
                svn.update(str(archive.svn_local_path))   # apparently can't handle unicode
                files.update(set(glob.iglob(os.path.join(archive.svn_local_path, '*.xml'))))


        for file in files:
            file_items = 0
            daos = 0
            try:
                if verbosity >= self.v_normal and len(files) > 1:
                    self.stdout.write('\nProcessing %s' % os.path.basename(file))

                ead = load_xmlobject_from_file(file, FindingAid)
                orig_xml = ead.serializeDocument()  # keep to check if changed

                for c in self.ead_file_items(ead):
                    # if item already contains any dao tags, skip it (no furher processing needed)
                    if c.did.dao_list:
                        continue

                    match = self.has_digitized_content(unicode(c.did.unittitle))
                    if match:
                        file_items += 1
                        try:
                            id_list = self.id_list(match.groupdict()['ids'])
                        except Exception as e:
                            self.stdout.write('Error parsing ids from "%s" : %s' % \
                                              (unicode(c.did.unittitle), e))
                            continue

                        # if no ids were found even though title seemed to have digitized content,
                        # error and skip to next
                        if not id_list:
                            self.stdout.write('Appears to have digitized content, but no ids found in "%s"' % \
                                              (unicode(c.did.unittitle)))
                            continue

                        # dictionary for any Keep info corresponding to these ids
                        id_info = {}

                        # look up each id in the Keep
                        for i in id_list:
                            q = solr.query(solr.Q(dm1_id="%s" % i) | solr.Q(pid="emory:%s" % i)) \
                                    .field_limit(['ark_uri', 'pid'])
                            if q.count() == 1:
                                id_info[i] = q[0]

                        # remove the plain-text digitized ids from unittitle content
                        # (handle as unicode to preserve any special characters)
                        # NOTE: because unittitle could contain nested tags (dates,
                        # titles, names, etc), iterate through the text nodes and
                        # remove the digitized note wherever it occurs
                        # - use lxml smart strings to update based on parent nodes
                        text_nodes = c.did.unittitle.node.xpath('text()')
                        for txt in text_nodes:
                            updated_txt = re.sub(self.digitized_ids, u'', txt)
                            if txt.is_text:
                                txt.getparent().text = updated_txt
                            else:
                                txt.getparent().tail = updated_txt

                        # ensure document has xlink namespace declared at the top
                        # or else it will be repeated for each dao

                        for i in id_list:
                            info = id_info.get(i, None)
                            # append a new dao for each id; audience will always be internal
                            dao_opts = {'audience': 'internal'}
                            href = None

                            if info:
                                # in some cases in production, a record is found but no
                                # ark_uri is indexed in solr (indicates ark_uri not in MODS)
                                try:
                                    href = info['ark_uri']
                                except KeyError:
                                    self.stdout.write('Warning: Keep record was found for %s but no ARK URI is indexed' \
                                        % i)

                            # if no record was found, *should* be a digital masters id
                            if href is None:
                                # if id already starts with dm, don't duplicate the prefix
                                if i.startswith('dm'):
                                    dao_opts['id'] = i
                                # if it's a digit, add dm prefix
                                elif i.isdigit():
                                    dao_opts['id'] = 'dm%s' % i
                                # otherwise, warn and add the id in pid notation
                                else:
                                    # only warn if we didn't already warn about info without ark uri
                                    if not info:
                                        self.stdout.write('Warning: non-digital masters id %s not found in the Keep' \
                                                           % i)
                                    # generate an ark anyway, since pids don't make valid ids
                                    href = 'http://pid.emory.edu/ark:/25593/%s' % i

                            c.did.dao_list.append(eadmap.DigitalArchivalObject(**dao_opts))
                            if href is not None:
                                c.did.dao_list[-1].href = href
                            # clean up any extra namespaces (exist-db ns)
                            cleanup_namespaces(c.did.dao_list[-1].node)

                            daos += 1

                # NOTE: could use pretty=True, but not used elsewhere in fa_admin,
                # so leaving off for consistency
                if orig_xml == ead.serializeDocument():
                    if verbosity > self.v_normal:
                        self.stdout.write("No changes made to %s" % file)
                    unchanged += 1
                else:
                    # in dry run, don't actually change the file
                    if not dry_run:
                        with open(file, 'w') as f:
                            ead.serializeDocument(f)
                    if verbosity >= self.v_normal:
                        self.stdout.write("Updated %s; found %d item%s with digitized content, added %d <dao>%s" \
                            % (file, file_items, 's' if file_items != 1 else '',
                               daos, 's' if daos != 1 else ''))
                    updated += 1

            except XMLSyntaxError:
                # xml is not well-formed
                self.stdout.write("Error: failed to load %s (document not well-formed XML?)" \
                                  % file)
                errored += 1
            # except Exception, e:
            #     # catch any other exceptions
            #     print "Error: failed to update %s : %s" % (file, e)
            #     errored += 1

        # TODO: might be nice to also report total number of daos added

        # summary of what was done
        self.stdout.write("\n%d document%s updated" % (updated, 's' if updated != 1 else ''))
        self.stdout.write("%d document%s unchanged" % (unchanged, 's' if unchanged != 1 else ''))
        self.stdout.write("%d document%s with errors" % (errored, 's' if errored != 1 else ''))

        if svn_commit:
            svn = svn_client()
            # seems to be the only way to set a commit log message via client
            def get_log_message(arg):
                # argument looks something like this:
                # [('foo', 'https://svn.library.emory.edu/svn/dev_ead-eua/trunk/eua0081affirmationvietnam.xml', 6, None, 4)]
                # ignoring since we will only use this function for a single commit
                return 'converted digitized item ids to <dao> tags'

            svn.log_msg_func = get_log_message

            for archive in Archive.objects.all():
                # update to make sure we have latest version of everything
                svn.commit(str(archive.svn_local_path))

    def has_digitized_content(self, text):
        # check if text (i.e. unittitle) seems to contain digitized content
        # returns regex match which should contains matched 'ids' in the groupdict
        return self.digitized_ids.search(text)

    def id_list(self, ids):
        # could match [digitized] with no ids; if so, return empty list
        if not ids:
            return []
        # parse out any id that are listed
        return self._parse_ids(ids)

    def _parse_ids(self, ids):
        # comma-separated list
        if ',' in ids or ';' in ids:
            id_list = []
            # figure out which delimiter we're splitting on
            delim = ',' if ',' in ids else ';'
            # NOTE: these parts could have delimiters, so recurse and
            # parse the split ids
            # e.g., handle ####, ####-####
            for part in [i.strip() for i in ids.split(delim)]:
                id_list.extend(self._parse_ids(part))

        # range of numbers
        elif '-' in ids:
            start, stop = [i.strip() for i in ids.split('-')]
            if not int(stop) > int(start):
                raise Exception('Range cannot be constructed from %s-%s' % (start, stop))

            length = len(start)
            # use range to get an inclusive list of the ids
            # then reformat with the same number of leading 000s
            fmt = '%%0%dd' % length
            id_list = [fmt % i for i in range(int(start), int(stop) + 1)]

        # otherwise, must be a single id listed only
        else:
            id_list = [ids.strip()]

        return id_list


    def ead_file_items(self, ead):
        '''generator that returns all file-level components in a findingaid,
        including any in series or subseries.
        '''
        if ead.dsc:
            if ead.dsc.hasSeries():
                for c in ead.dsc.c:
                    for subc in self.series_file_items(c):
                        yield subc
            else:
                for c in ead.dsc.c:
                    yield c

    def series_file_items(self, series):
        '''generator that returns all file-level components in a series,
        including any in subseries'''
        if series.hasSubseries():
            for c in series.c:
                for subc in self.series_file_items(c):
                    yield subc
        else:
            for c in series.c:
                yield c


def solr_interface():
    '''Wrapper function to initialize a
    :class:`sunburnt.SolrInterface` based on django settings and
    evironment.  Uses **KEEP_SOLR_SERVER_URL** and **SOLR_CA_CERT_PATH** if
    one is set.  Additionally, if an **HTTP_PROXY** is set in the
    environment, it will be configured.
    '''
    # NOTE: borrowed pretty much intact from keep.util
    http_opts = {}
    if hasattr(settings, 'SOLR_CA_CERT_PATH'):
        http_opts['ca_certs'] = settings.SOLR_CA_CERT_PATH
    if getattr(settings, 'SOLR_DISABLE_CERT_CHECK', False):
        http_opts['disable_ssl_certificate_validation'] = True

    # use http proxy if set in ENV
    http_proxy = os.getenv('HTTP_PROXY', None)
    solr_url = urlparse(settings.KEEP_SOLR_SERVER_URL)
    # NOTE: using Squid with httplib2 requires no-tunneling proxy option
    # - non-tunnel proxy does not work with https
    if http_proxy and solr_url.scheme == 'http':
        parsed_proxy = urlparse(http_proxy)
        proxy_info = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL,
                                        proxy_host=parsed_proxy.hostname,
                                        proxy_port=parsed_proxy.port)
        http_opts['proxy_info'] = proxy_info
    http = httplib2.Http(**http_opts)

    solr_opts = {'http_connection': http}

    solr = sunburnt.SolrInterface(settings.KEEP_SOLR_SERVER_URL,
                                  **solr_opts)
    return solr

