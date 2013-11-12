# file findingaids/fa_admin/auth.py
#
#   Copyright 2013 Emory University Library
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

from django.core.exceptions import ObjectDoesNotExist

from eulexistdb.exceptions import DoesNotExist

from findingaids.fa.models import FindingAid, Archive
from findingaids.fa.utils import normalize_whitespace


def archive_access(user, archive=None, *args, **kwargs):
    '''Check if a user has permission to take action (e.g., prep, preview, publish)
    on a specific archive.  Superusers are have access to all archives.

    :param user: logged in user
    :param archive: slug identifier for an :class:`~findingaids.fa.models.Archive`.
    :param request: http request; optionally used to look for an 'archive'
        request parameter, if archive param is None

    :returns: true if access is allowed, false if not
    :rtype: bool
    '''
    # always false if user is not logged in
    if not user.is_authenticated():
        return False

    # always allowed if user is superuser
    # NOTE: even if archive is not specified or does not exist-
    # allow, and let the view handle that logic
    if user.is_superuser:
        return True

    # check for request in kwargs in case we need it for archive info
    request = kwargs.get('request', None)

    # if archive parameter is not set, check for an archive request parameter
    if archive is None and request is not None:
        # NOTE: not using request.REQUEST because it is deprecated in Django 1.7
        archive = request.GET.get('archive', None)
        if archive is None:
            archive = request.POST.get('archive', None)

    # error if we don't have an archive slug
    if archive is None:
        raise Exception('Archive not specified')

    try:
        arc = user.archivist
    except ObjectDoesNotExist:
        return False

    if arc.archives.filter(slug=archive).count():
        return True

    return False

def archive_access_by_ead(user, id, *args, **kwargs):
    '''Check if a user has permissions for a specific archive based on an
    EAD document.  Expects an eadid, which will be used to determine what
    Archive the document is associated with; then hands off
    to :meth:`archive_access`.
    '''
    archive = None

    try:
        ead = FindingAid.objects.only('repository').get(eadid=id)

        if ead.repository:
            # NOTE: for some reason the partial return doesn't get normalized
            # normalize it here to ensure we get a match
            archive_name = normalize_whitespace(ead.repository[0])
            try:
                archive = Archive.objects.get(name=archive_name).slug
            except ObjectDoesNotExist:
                pass

    except DoesNotExist:
        pass

    # hand off even if archive couldn't be determined - logic for non-admin
    # and superuser will still be accurate & useful
    return archive_access(user, archive, *args, **kwargs)
