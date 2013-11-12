# file findingaids/fa_admin/views.py
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

import os
import difflib
import logging
from lxml.etree import XMLSyntaxError

from django.http import HttpResponse, HttpResponseServerError, Http404, \
    HttpResponseBadRequest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import logout_then_login
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST


from eulcommon.djangoextras.auth import permission_required_with_403, \
   login_required_with_ajax, user_passes_test_with_ajax
from eulexistdb.db import ExistDB, ExistDBException
from eulcommon.djangoextras.http import HttpResponseSeeOtherRedirect
from eullocal.django.log import message_logging
from eullocal.django.taskresult.models import TaskResult
from eulxml.xmlmap.core import load_xmlobject_from_file, load_xmlobject_from_string
from eulexistdb.exceptions import DoesNotExist

from findingaids.fa.models import FindingAid, Deleted, Archive
from findingaids.fa.utils import pages_to_show, get_findingaid, paginate_queryset
from findingaids.fa_admin.auth import archive_access
from findingaids.fa_admin.forms import DeleteForm
from findingaids.fa_admin.models import Archivist
from findingaids.fa_admin.source import files_to_publish
from findingaids.fa_admin.tasks import reload_cached_pdf
from findingaids.fa_admin import utils


@login_required
def main(request):
    """
    Main admin page.

    Displayes a paginated list of files configured source directory (sorted by
    most recently modified) to be previewed, published, or prepared for
    preview/publish.
    """
    # get sorted archive list for this user
    try:
        archives = request.user.archivist.sorted_archives()
    except ObjectDoesNotExist:
        # i.e. no user -> archivist association
        if request.user.is_superuser:
            archives = Archive.objects.all()
        else:
            archives = []

    # files for publication now loaded in jquery ui tab via ajax

    # get the 10 most recent task results to display status
    recent_tasks = TaskResult.objects.order_by('-created')[:10]

    return render(request, 'fa_admin/index.html', {
        'archives': archives,
        'task_results': recent_tasks})


# NOTE: viewing the file list sort of implies prep/preview/publish permissions
# but currently does not actually *require* them
@login_required_with_ajax()
@user_passes_test_with_ajax(archive_access)
def list_files(request, archive):
    '''List files associated with an archive to be prepped and previewed
    for publication.  Expected to be retrieved via ajax and loaded in a
    jquery ui tab, so only returns a partial html page without site theme.
    '''
    archive = get_object_or_404(Archive, slug=archive)

    files = files_to_publish(archive)
    # sort by last modified time
    files = sorted(files, key=lambda file: file.mtime, reverse=True)
    paginator = Paginator(files, 30, orphans=5)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    show_pages = pages_to_show(paginator, page)
    # If page request (9999) is out of range, deliver last page of results.
    try:
        recent_files = paginator.page(page)
    except (EmptyPage, InvalidPage):
        recent_files = paginator.page(paginator.num_pages)

    return render(request, 'fa_admin/snippets/list_files_tab.html', {
        'files': recent_files,
        'show_pages': show_pages})

@require_POST
@login_required_with_ajax()
def archive_order(request):
    # expects a comma-separated list of archive slugs
    ids = request.POST.get('ids', None)
    if not ids:
        return HttpResponseBadRequest()

    slugs = ids.split(',')
    # find all archives matching any of the slugs passed in
    archives = Archive.objects.filter(slug__in=slugs)
    # re-sort according to the order in the request
    archives = sorted(archives, key=lambda arch: slugs.index(arch.slug))

    # save order to user account
    try:
        arc = request.user.archivist
    except ObjectDoesNotExist:
        # if for some reason user model does not have an archivist,
        # create one so we can store the order preference
        arc = Archivist()
        request.user.archivist = arc

    arc.order = ','.join([str(a.id) for a in archives])
    request.user.archivist.save()

    return HttpResponse('Updated order')


@login_required
def logout(request):
    """Admin Logout view. Displays a message and then calls
    :meth:`django.contrib.auth.views.logout_then_login`.
    """
    messages.success(request, 'You are now logged out.')
    return logout_then_login(request)


@permission_required_with_403('auth.user.can_change')
def list_staff(request):
    """
    Displays a list of user accounts, with summary information about each user
    and a link to edit each user account.
    """
    users = get_user_model().objects.all()
    app, model = settings.AUTH_USER_MODEL.lower().split('.')
    change_url = 'admin:%s_%s_change' % (app, model)

    return render(request, 'fa_admin/list-users.html',
        {'users': users, 'user_change_url': change_url})


def _prepublication_check(request, filename, mode='publish', xml=None,
        archive_slug=None):
    """
    Pre-publication check logic common to :meth:`publish` and :meth:`preview`.

    Generates a full path to the file in the configured EAD source directory,
    and the expected published location in eXist, and then runs
    :meth:`~findingaids.fa_admin.utils.check_ead` to check the xml for errors.

    If there are errors, will generate an error response that can be displayed.

    :param request: request object passed into the view (for generating error response)
    :param filename: base filename of the ead file to be checked
    :param mode: optional mode, for display on error page (defaults to publish)
    :rtype: list
    :returns: list of the following:
      - boolean ok (if True, all checks passed)
      - HttpResponse response error response to display, if there were errors
      - dbpath - full path to publication location in configured eXist db
      - fullpath - full path to the file in the configured source directory
    """

    if archive_slug is not None:
        base_path = Archive.objects.get(slug=archive_slug).svn_local_path
    else:
        # otherwise fallback to single configured directory
        base_path = settings.FINDINGAID_EAD_SOURCE

    # full path to the local file
    fullpath = os.path.join(base_path, filename)
    # full path in exist db collection
    dbpath = settings.EXISTDB_ROOT_COLLECTION + "/" + filename
    errors = utils.check_ead(fullpath, dbpath, xml)
    if errors:
        ok = False
        response = render(request, 'fa_admin/publish-errors.html',
                {'errors': errors, 'filename': filename, 'mode': mode})
    else:
        ok = True
        response = None
    return [ok, response, dbpath, fullpath]

@permission_required_with_403('fa_admin.can_publish')
@require_POST
def publish(request):
    """
    Admin publication form.  Allows publishing an EAD file by updating or adding
    it to the configured eXist database so it will be immediately visible on
    the public site.  Files can only be published if they pass an EAD sanity check,
    implemented in :meth:`~findingaids.fa_admin.utils.check_ead`.

    On POST, sanity-check the EAD file specified in request from the configured
    and (if it passes all checks), publish it to make it immediately visible on
    the site.  If publish is successful, redirects the user to main admin page
    with a success message that links to the published document on the site.
    If the sanity-check fails, displays a page with any problems found.
    """
    # formerly supported publish from filename, but now only supports
    # publish from preview
    if 'preview_id' not in request.POST:
        messages.error(request, "No preview document specified for publication")
        return HttpResponseSeeOtherRedirect(reverse('fa-admin:index'))

    id = request.POST['preview_id']

    # retrieve info about the document from preview collection
    try:
        # because of the way eulcore.existdb.queryset constructs returns with 'also' fields,
        # it is simpler and better to retrieve document name separately
        ead = get_findingaid(id, preview=True)
        ead_docname = get_findingaid(id, preview=True, only=['document_name'])
        filename = ead_docname.document_name
    except Http404:     # not found in exist
        ead = None
        messages.error(request,
            "Publish failed. Could not retrieve <b>%s</b> from preview collection. Please reload and try again." % id)

    if ead is None:
        # if ead could not be retrieved from preview mode, skip processing
        return HttpResponseSeeOtherRedirect(reverse('fa-admin:index'))

    xml = ead.serialize()

    # TODO: check that user is allowed to publish the document
    # - will have to be based on subarea

    errors = []
    try:
        ok, response, dbpath, fullpath = _prepublication_check(request, filename, xml=xml)
        if ok is not True:
            # publication check failed - do not publish
            return response

        # only load to exist if there are no errors found
        db = ExistDB()
        # get information to determine if an existing file is being replaced
        replaced = db.describeDocument(dbpath)

        try:
            # move the document from preview collection to configured public collection
            success = db.moveDocument(settings.EXISTDB_PREVIEW_COLLECTION,
                    settings.EXISTDB_ROOT_COLLECTION, filename)
            # FindingAid instance ead already set above
        except ExistDBException, e:
            # special-case error message
            errors.append("Failed to move document %s from preview collection to main collection." \
                            % filename)
            # re-raise and let outer exception handling take care of it
            raise e

    except ExistDBException, e:
        errors.append(e.message())
        success = False

    if success:
        # request the cache to reload the PDF - queue asynchronous task
        result = reload_cached_pdf.delay(ead.eadid.value)
        task = TaskResult(label='PDF reload', object_id=ead.eadid.value,
            url=reverse('fa:findingaid', kwargs={'id': ead.eadid.value}),
            task_id=result.task_id)
        task.save()

        ead_url = reverse('fa:findingaid', kwargs={'id': ead.eadid.value})
        change = "updated" if replaced else "added"
        messages.success(request, 'Successfully %s <b>%s</b>. View <a href="%s">%s</a>.'
                % (change, filename, ead_url, unicode(ead.unittitle)))

        # redirect to main admin page and display messages
        return HttpResponseSeeOtherRedirect(reverse('fa-admin:index'))
    else:
        return render(request, 'fa_admin/publish-errors.html',
            {'errors': errors, 'filename': filename, 'mode': 'publish', 'exception': e})

@permission_required_with_403('fa_admin.can_preview')
@user_passes_test_with_ajax(archive_access)
def preview(request):
    if request.method == 'POST':
        filename = request.POST['filename']
        archive_slug = request.POST.get('archive', None)

        errors = []

        try:
            # only load to exist if document passes publication check
            ok, response, dbpath, fullpath = _prepublication_check(request, filename, mode='preview',
                archive_slug=archive_slug)
            if ok is not True:
                return response

            db = ExistDB()
            # load the document to the *preview* collection in eXist with the same fileneame
            preview_dbpath = settings.EXISTDB_PREVIEW_COLLECTION + "/" + filename
            # make sure the preview collection exists, but don't complain if it's already there
            success = db.load(open(fullpath, 'r'), preview_dbpath, overwrite=True)
        except ExistDBException, e:
            success = False
            errors.append(e.message())

        if success:
            # load the file as a FindingAid object so we can generate the preview url
            ead = load_xmlobject_from_file(fullpath, FindingAid)
            messages.success(request, 'Successfully loaded <b>%s</b> for preview.' % filename)
            # redirect to document preview page with code 303 (See Other)
            return HttpResponseSeeOtherRedirect(reverse('fa-admin:preview:findingaid', kwargs={'id': ead.eadid}))
        else:
            return render(request, 'fa_admin/publish-errors.html',
                    {'errors': errors, 'filename': filename, 'mode': 'preview', 'exception': e})

    # TODO: preview list needs to either go away (not currently used)
    # or be filtered by archive
    else:
        fa = get_findingaid(preview=True, only=['eadid', 'list_title', 'last_modified'],
                            order_by='last_modified')
        return render(request, 'fa_admin/preview_list.html',
                {'findingaids': fa, 'querytime': [fa.queryTime()]})
        return HttpResponse('preview placeholder- list of files to be added here')


@login_required
@cache_page(1)  # cache this view and use it as source for prep diff/summary views
@user_passes_test_with_ajax(archive_access)
def prepared_eadxml(request, filename, archive=None):
    """Serve out a prepared version of the EAD file in the configured EAD source
    directory.  Response header is set so the user should be prompted to download
    the xml, with a filename matching that of the original document.

    Steps taken to prepare a document are documented in
    :meth:`~findingaids.fa_admin.utils.prep_ead`.

    :param filename: name of the file to prep; should be base filename only,
        document will be pulled from the configured source directory.
    """
    # find relative to svn path if associated with an archive
    if archive is None:
        archive = request.GET.get('archive', None)
    if archive:
        base_path = Archive.objects.get(slug=archive).svn_local_path
    else:
        # otherwise fallback to single configured directory
        base_path = settings.FINDINGAID_EAD_SOURCE

    fullpath = os.path.join(base_path, filename)
    try:
        ead = load_xmlobject_from_file(fullpath, FindingAid)  # validate or not?
    except XMLSyntaxError, e:
        # xml is not well-formed : return 500 with error message
        return HttpResponseServerError("Could not load document: %s" % e)

    with message_logging(request, 'findingaids.fa_admin.utils', logging.INFO):
        try:
            ead = utils.prep_ead(ead, filename)
        except Exception as e:
            # any exception on prep is most likely ark generation
            return HttpResponseServerError('Failed to prep the document: ' + str(e))

    prepped_xml = ead.serializeDocument()

    response = HttpResponse(prepped_xml, mimetype='application/xml')
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

@login_required
@user_passes_test_with_ajax(archive_access)
def prepared_ead(request, filename, mode):
    """Display information about changes made by preparing an EAD file for
    publication.  If no changes are made, user will be redirected to main admin
    page with a message to that effect.

    In **summary** mode, displays a brief, color-coded summary of changes between
    original and prepped version of the file.  In **diff** mode, displays a full,
    side-by-side diff generated by :class:`difflib.HtmlDiff`.  (Note: because it
    is very large, the full diff is *not* embedded in the site template, and is
    intended to be opened in a new window.)

    :param filename: name of the file to prep; should be base filename only,
        document will be pulled from the configured source directory.
    :param mode: one of **diff** or **summary**

    """

    # determine full path based on archive / svn
    archive_slug = request.GET.get('archive', None)
    if archive_slug:
        base_path = Archive.objects.get(slug=archive_slug).svn_local_path
    else:
        # otherwise fallback to single configured directory
        base_path = settings.FINDINGAID_EAD_SOURCE

    fullpath = os.path.join(base_path, filename)
    changes = []

    # TODO: expire cache if file has changed since prepped eadxml was cached
    prep_ead = prepared_eadxml(request, filename, archive_slug)

    if prep_ead.status_code == 200:
        orig_ead = load_xmlobject_from_file(fullpath, FindingAid)  # validate or not?
        original_xml = orig_ead.serializeDocument()  # store as serialized by xml object, so xml output will be the same

        prep_xml = prep_ead.content
        ead = load_xmlobject_from_string(prep_xml, FindingAid)  # validate?
        if mode == 'diff':
            diff = difflib.HtmlDiff(8, 80)  # set columns to wrap at 80 characters
            # generate a html table with line-by-line comparison (meant to be called in a new window)
            changes = diff.make_file(original_xml.split('\n'), prep_xml.split('\n'))
            return HttpResponse(changes)
        elif mode == 'summary':
            # prepared EAD should pass sanity checks required for publication
            errors = utils.check_eadxml(ead)
            changes = list(difflib.unified_diff(original_xml.split('\n'), prep_xml.split('\n')))
            if not changes:
                messages.info(request, 'No changes made to <b>%s</b>; EAD is already prepared.' % filename)
                # redirect to main admin page with code 303 (See Other)
                return HttpResponseSeeOtherRedirect(reverse('fa-admin:index'))
    elif prep_ead.status_code == 500:
        # something went wrong with generating prep xml; could be one of:
        # - non-well-formed xml (failed to load original document at all)
        # - error generating an ARK for the document
        errors = [prep_ead.content]
    else:
        # this shouldn't happen; not 200 or 500 == something went dreadfully wrong
        errors = ['Something went wrong trying to load the specified document.',
                  prep_ead.content]     # pass along the output in case it is useful?

    return render(request, 'fa_admin/prepared.html', {
        'filename': filename,
        'changes': changes, 'errors': errors,
        'xml_status': prep_ead.status_code,
        'archive_slug': archive_slug})


@login_required
def list_published(request):
    """List all published EADs."""
    fa = FindingAid.objects.order_by('eadid').only('document_name', 'eadid', 'last_modified')
    fa_subset, paginator = paginate_queryset(request, fa, per_page=30, orphans=5)
    show_pages = pages_to_show(paginator, fa_subset.number)

    return render(request, 'fa_admin/published_list.html', {'findingaids': fa_subset,
        'querytime': [fa.queryTime()], 'show_pages': show_pages})


@permission_required_with_403('fa_admin.can_delete')
def delete_ead(request, id):
    """ Delete a published EAD.

    On GET, display a form with information about the document to be removed.

    On POST, actually remove the specified EAD document from eXist and create (or
    update) a deleted record for that document in the relational DB.
    """
    # retrieve the finding aid to be deleted with fields needed for
    # form display or actual deletion
    try:
        fa = FindingAid.objects.only('eadid', 'unittitle',
                            'document_name', 'collection_name').get(eadid=id)

        # if this record has been deleted before, get that record and update it
        deleted_info, created = Deleted.objects.get_or_create(eadid=fa.eadid)
        deleted_info.title = unicode(fa.unittitle)   # update with title from current document

        render_form = False

        # on GET, display delete form
        if request.method == 'GET':
            # pre-populate the form with info from the finding aid to be removed
            delete_form = DeleteForm(instance=deleted_info)
            render_form = True

        else:   # POST : actually delete the document
            delete_form = DeleteForm(request.POST, instance=deleted_info)
            if delete_form.is_valid():
                delete_form.save()
                db = ExistDB()
                try:
                    success = db.removeDocument(fa.collection_name + '/' + fa.document_name)
                    if success:
                        DeleteForm(request.POST, instance=deleted_info).save()
                        messages.success(request, 'Successfully removed <b>%s</b>.' % id)
                    else:
                        # remove exited normally but was not successful
                        messages.error(request, 'Error: failed to removed <b>%s</b>.' % id)
                except ExistDBException, e:
                    messages.error(request, "Error: failed to remove <b>%s</b> - %s." \
                                % (id, e.message()))
            else:
                render_form = True

        if render_form:
            return render(request, 'fa_admin/delete.html',
                {'fa': fa, 'form': delete_form})
    except DoesNotExist:
        # requested finding aid was not found (on either GET or POST)
        messages.error(request, "Error: could not retrieve <b>%s</b> for deletion." % id)

    # if we get to this point, either there was an error or the document was
    # successfully deleted - in any of those cases, redirect to publish list
    return HttpResponseSeeOtherRedirect(reverse('fa-admin:list-published'))
