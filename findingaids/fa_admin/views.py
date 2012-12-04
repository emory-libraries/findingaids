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
import glob
import difflib
import logging
from lxml.etree import XMLSyntaxError

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page

from eulcommon.djangoextras.auth import permission_required_with_403
from eulexistdb.db import ExistDB, ExistDBException
from eulcommon.djangoextras.http import HttpResponseSeeOtherRedirect
from eullocal.django.log import message_logging
from eullocal.django.taskresult.models import TaskResult
from eulxml.xmlmap.core import load_xmlobject_from_file, load_xmlobject_from_string
from eulexistdb.exceptions import DoesNotExist

from findingaids.fa.models import FindingAid, Deleted
from findingaids.fa.utils import pages_to_show, get_findingaid, paginate_queryset
from findingaids.fa_admin.forms import FAUserChangeForm, DeleteForm
from findingaids.fa_admin.models import EadFile
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
    recent_files = []
    show_pages = []
    if not hasattr(settings, 'FINDINGAID_EAD_SOURCE'):
        error = "Please configure EAD source directory in local settings."
    else:
        dir = settings.FINDINGAID_EAD_SOURCE
        if os.access(dir, os.F_OK | os.R_OK):
            recent_files = _get_recent_xml_files(dir)
            error = None
        else:
            error = "EAD source directory '%s' does not exist or is not readable; please check config file." % dir

    paginator = Paginator(recent_files, 30, orphans=5)
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

    # get the 10 most recent task results to display status
    recent_tasks = TaskResult.objects.order_by('-created')[:10]
    return render_to_response('fa_admin/index.html', {'files': recent_files,
                            'show_pages': show_pages,
                            'error': error,
                            'task_results': recent_tasks},
                            context_instance=RequestContext(request))


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
    users = User.objects.all()
    return render_to_response('fa_admin/list-users.html', {'users': users},
                              context_instance=RequestContext(request))


@permission_required_with_403('auth.user.can_change')
def edit_user(request, user_id):
    """Display and process a form for editing a user account.

    On GET, display the edit form. On POST, process the form.
    """
    user = User.objects.get(id=user_id)
    if request.method == 'POST':  # If the form has been submitted...
        userForm = FAUserChangeForm(request.POST, instance=user)  # A form bound to the POST data
        if userForm.is_valid():  # form is valid - save data
            userForm.save()
            messages.success(request, "Changes to user '%s' have been saved." \
                            % user.username)
            return HttpResponseRedirect(reverse('fa-admin:index'))
        else:
            # form validation errors -- allow to fall through to render form
            pass
    else:   # GET - display the form
        userForm = FAUserChangeForm(instance=user)

    return render_to_response('fa_admin/account-management.html',
                              {'form': userForm, 'user_id': user_id},
                              context_instance=RequestContext(request))


def _prepublication_check(request, filename, mode='publish', xml=None):
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

    # full path to the local file
    fullpath = os.path.join(settings.FINDINGAID_EAD_SOURCE, filename)
    # full path in exist db collection
    dbpath = settings.EXISTDB_ROOT_COLLECTION + "/" + filename
    errors = utils.check_ead(fullpath, dbpath, xml)
    if errors:
        ok = False
        response = render_to_response('fa_admin/publish-errors.html',
                {'errors': errors, 'filename': filename, 'mode': mode},
                context_instance=RequestContext(request))
    else:
        ok = True
        response = None
    return [ok, response, dbpath, fullpath]


@permission_required_with_403('fa_admin.can_publish')
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

    On GET, displays a list of files available for publication.
    """
    if request.method == 'POST':
        if 'filename' in request.POST:
            publish_mode = 'file'
            filename = request.POST['filename']
            xml = None

        elif 'preview_id' in request.POST:
            publish_mode = 'preview'
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

            if publish_mode == 'file':
                # load the document to the configured collection in eXist with the same fileneame
                success = db.load(open(fullpath, 'r'), dbpath, overwrite=True)
                # load the file as a FindingAid object so we can generate a url to the document
                ead = load_xmlobject_from_file(fullpath, FindingAid)

            elif publish_mode == 'preview' and ead is not None:
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
            return render_to_response('fa_admin/publish-errors.html',
                {'errors': errors, 'filename': filename, 'mode': 'publish', 'exception': e},
                context_instance=RequestContext(request))
    else:
        # if not POST, display list of files available for publication
        # for now, just using main admin page
        return main(request)


@permission_required_with_403('fa_admin.can_preview')
def preview(request):
    if request.method == 'POST':
        filename = request.POST['filename']
        errors = []

        try:
            # only load to exist if document passes publication check
            ok, response, dbpath, fullpath = _prepublication_check(request, filename, mode='preview')
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
            return render_to_response('fa_admin/publish-errors.html',
                    {'errors': errors, 'filename': filename, 'mode': 'preview', 'exception': e},
                    context_instance=RequestContext(request))
    else:
        fa = get_findingaid(preview=True, only=['eadid', 'list_title', 'last_modified'],
                            order_by='last_modified')
        return render_to_response('fa_admin/preview_list.html',
                {'findingaids': fa, 'querytime': [fa.queryTime()]},
                context_instance=RequestContext(request))
        return HttpResponse('preview placeholder- list of files to be added here')


@login_required
@cache_page(5)  # cache this view and use it as source for prep diff/summary views
def prepared_eadxml(request, filename):
    """Serve out a prepared version of the EAD file in the configured EAD source
    directory.  Response header is set so the user should be prompted to download
    the xml, with a filename matching that of the original document.

    Steps taken to prepare a document are documented in
    :meth:`~findingaids.fa_admin.utils.prep_ead`.

    :param filename: name of the file to prep; should be base filename only,
        document will be pulled from the configured source directory.
    """
    fullpath = os.path.join(settings.FINDINGAID_EAD_SOURCE, filename)
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
    fullpath = os.path.join(settings.FINDINGAID_EAD_SOURCE, filename)
    changes = []

    # TODO: expire cache if file has changed since prepped eadxml was cached
    prep_ead = prepared_eadxml(request, filename)

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

    return render_to_response('fa_admin/prepared.html', {'filename': filename,
                                'changes': changes, 'errors': errors,
                                'xml_status': prep_ead.status_code},
                                context_instance=RequestContext(request))


def _get_recent_xml_files(dir):
    "Return recently modified xml files from the specified directory."
    # get all xml files in the specified directory
    filenames = glob.glob(os.path.join(dir, '*.xml'))
    # modified time, base name of the file
    files = [EadFile(os.path.basename(file), os.path.getmtime(file)) for file in filenames]
    # sort by last modified time
    return sorted(files, key=lambda file: file.mtime, reverse=True)


@login_required
def list_published(request):
    """List all published EADs."""
    fa = FindingAid.objects.order_by('eadid').only('document_name', 'eadid', 'last_modified')
    fa_subset, paginator = paginate_queryset(request, fa, per_page=30, orphans=5)
    show_pages = pages_to_show(paginator, fa_subset.number)

    return render_to_response('fa_admin/published_list.html', {'findingaids': fa_subset,
                              'querytime': [fa.queryTime()], 'show_pages': show_pages},
                              context_instance=RequestContext(request))


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
            return render_to_response('fa_admin/delete.html',
                                    {'fa': fa, 'form': delete_form},
                                    context_instance=RequestContext(request))
    except DoesNotExist:
        # requested finding aid was not found (on either GET or POST)
        messages.error(request, "Error: could not retrieve <b>%s</b> for deletion." % id)

    # if we get to this point, either there was an error or the document was
    # successfully deleted - in any of those cases, redirect to publish list
    return HttpResponseSeeOtherRedirect(reverse('fa-admin:list-published'))
