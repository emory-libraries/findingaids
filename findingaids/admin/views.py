import os
import glob
from datetime import datetime
import difflib

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.decorators.cache import cache_page


from eulcore.django.existdb.db import ExistDB
from eulcore.xmlmap.core import load_xmlobject_from_file, load_xmlobject_from_string

from findingaids.fa.models import FindingAid
from findingaids.admin.utils import check_ead, check_eadxml, clean_ead


@login_required
def main(request):
    """
    Main admin page.

    Displayes a paginated list of files configured source directory (sorted by
    most recently modified) to be previewed, published, or cleaned.
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
    show_pages = _pages_to_show(paginator, page)
    # If page request (9999) is out of range, deliver last page of results.
    try:
        recent_files = paginator.page(page)
    except (EmptyPage, InvalidPage):
        recent_files = paginator.page(paginator.num_pages)

    return render_to_response('admin/index.html', {'files' : recent_files,
                            'show_pages' : show_pages,
                            'error' : error},
                            context_instance=RequestContext(request))


def logout(request):
    """
    Admin Login page.

    Logout user and redirect to admin login page.
    
    """
    login_url = settings.LOGIN_URL
    messages.success(request, 'You have logged out of finding aids.')
    return logout_then_login(request)


def list_staff(request):
    
    users = User.objects.all()
    print users

    return render_to_response('admin/list-users.html', {'users' : users,},context_instance=RequestContext(request))


def edit_user(request):
    if request.user.is_superuser:
        if request.method == 'POST': # If the form has been submitted...
            userForm = UserChangeForm(request.POST) # A form bound to the POST data
            if userForm.is_valid(): # All validation rules pass
                # Process the data in form.cleaned_data
                # ...
                return HttpResponseRedirect('/admin/') # Redirect after PO
        else:
            userForm = UserChangeForm()
          
        return render_to_response('admin/account-management.html', {'form' : userForm,}, context_instance=RequestContext(request))
    else:
        messages.warning(request, 'You do not have permission to view this page.')
        return HttpResponseRedirect("/admin/")
        
        
@login_required
def publish(request):
    """
    Admin publication form.  Allows publishing an EAD file by updating or adding
    it to the configured eXist database so it will be immediately visible on
    the public site.  Files can only be published if they pass an EAD sanity check,
    implemented in :meth:`~findingaids.admin.utils.check_ead`.

    On POST, sanity-check the EAD file specified in request from the configured
    and (if it passes all checks), publish it to make it immediately visible on
    the site.  If publish is successful, redirects the user to main admin page
    with a success message that links to the published document on the site.
    If the sanity-check fails, displays a page with any problems found.

    On GET, displays a list of files available for publication.
    """
    if request.method == 'POST':
        filename = request.POST['filename']
        # full path to the local file
        fullpath = os.path.join(settings.FINDINGAID_EAD_SOURCE, filename)
        # full path in exist db collection
        dbpath = settings.EXISTDB_ROOT_COLLECTION + "/" + filename

        errors = check_ead(fullpath, dbpath)
        if errors:
            return render_to_response('admin/publish-errors.html', {'errors': errors, 'filename': filename},
                            context_instance=RequestContext(request))
        # only load to exist if there are no errors found
        db = ExistDB()
        # get information to determine if a db file is being replaced
        replaced = db.describeDocument(dbpath)
        # load the document to the configured collection in eXist with the same fileneame
        # NOTE: specifying to always overwrite copy in eXist 
        success = db.load(open(fullpath, 'r'), dbpath, True)
        if success:          
            # load the file as a FindingAid object so we can generate a url to the document
            ead = load_xmlobject_from_file(fullpath, FindingAid)
            ead_url = reverse('fa:view-fa', kwargs={ 'id' : ead.eadid })
            if replaced:
                change = "updated"
            else:
                change = "added"
            messages.success(request, 'Successfully %s <b>%s</b>. View <a href="%s">%s</a>.'
                    % (change, filename, ead_url, ead.unittitle))
        else:
            messages.error("Error publishing <b>%s</b>." % filename)

        # redirect to main admin page with code 303 (See Other)
        response = HttpResponse(status=303)
        response['Location'] = reverse('admin:index')
        return response
    else:
        # if not POST, display list of files available for publication
        # for now, just using main admin page
        return main(request)

@login_required
@cache_page(60)        # cache this view and use it as source for cleaned diff/summary views
# FIXME: what is a reasonable duration?
def cleaned_eadxml(request, filename):
    """Serve out a cleaned version of the EAD file in the configured EAD source
    directory.  Response header is set so the user should be prompted to download
    the xml, with a filename matching that of the original document.

    Steps taken to clean a document are documented in
    :meth:`~findingaids.admin.utils.clean_ead`.

    :param filename: name of the file to clean; should be base filename only,
        document will be pulled from the configured source directory.    
    """
    fullpath = os.path.join(settings.FINDINGAID_EAD_SOURCE, filename)
    ead = load_xmlobject_from_file(fullpath, FindingAid) # validate or not?
    #original_xml = ead.serialize()  # store as serialized by xml object, so xml output will be the same
    # FIXME: losing doctype declaration on serialize?!?
    ead = clean_ead(ead, filename)
    cleaned_xml = ead.serialize()

    response = HttpResponse(cleaned_xml, mimetype='application/xml')
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

@login_required
def cleaned_ead(request, filename, mode):
    """Display information about changes made by cleaning an EAD file.  If no
    changes are made, user will be redirected to main admin page with a message
    to that effect.

    In **summary** mode, displays a brief, color-coded summary of changes between
    original and cleaned version of the file.  In **diff** mode, displays a full,
    side-by-side diff generated by :class:`difflib.HtmlDiff`.  (Note: because it
    is very large, the full diff is *not* embedded in the site template, and is
    intended to be opened in a new window.)

    :param filename: name of the file to clean; should be base filename only,
        document will be pulled from the configured source directory.
    :param mode: one of **diff** or **summary**
    
    """
    fullpath = os.path.join(settings.FINDINGAID_EAD_SOURCE, filename)
    cleaned_ead = cleaned_eadxml(request, filename)
    orig_ead = load_xmlobject_from_file(fullpath, FindingAid) # validate or not?
    original_xml = orig_ead.serialize()  # store as serialized by xml object, so xml output will be the same
    # FIXME: losing doctype declaration on serialize?!?
    
    cleaned_xml = cleaned_ead.content
    ead = load_xmlobject_from_string(cleaned_xml, FindingAid) # validate?        
    if mode == 'diff':
        diff = difflib.HtmlDiff(8, 80)  # set columns to wrap at 80 characters
        # generate a html table with line-by-line comparison (meant to be called in a new window)
        changes = diff.make_file(original_xml.split('\n'), cleaned_xml.split('\n'))
        return HttpResponse(changes)
    elif mode == 'summary':
        # cleaned up EAD should pass sanity checks required for publication
        errors = check_eadxml(ead)
        changes = list(difflib.unified_diff(original_xml.split('\n'), cleaned_xml.split('\n')))
        if not changes:
            messages.info(request, 'No changes made to <b>%s</b>; EAD is already clean.' % filename)
            # redirect to main admin page with code 303 (See Other)
            response = HttpResponse(status=303)
            response['Location'] = reverse('admin:index')
            return response
        return render_to_response('admin/cleaned.html', {'filename' : filename,
                                'changes' : changes, 'errors' : errors},
                                context_instance=RequestContext(request))

def _get_recent_xml_files(dir):
    "Return recently modified xml files from the specified directory."
    # get all xml files in the specified directory
    filenames = glob.glob(os.path.join(dir, '*.xml'))
    # modified time, base name of the file
    files = [ (os.path.getmtime(file), os.path.basename(file)) for file in filenames ]
    # reverse sort - most recently modified first
    files.sort(reverse=True)
    # convert modified time into a datetime object
    recent_files = [ (filename, datetime.utcfromtimestamp(mtime)) for mtime, filename in files ]
    return recent_files

def _pages_to_show(paginator, page):
    # generate a list of pages to show around the current page
    # show 3 numbers on either side of current number, or more if close to end/beginning
    show_pages = []
    if page != 1:        
        before = 4
        if page >= (paginator.num_pages - 3):   # current page is within 3 of end
            # increase number to show before current page based on distance to end
            before += (3 - (paginator.num_pages - page))
        for i in range(before, 1, -1):
            if (page - i) >= 1:
                show_pages.append(page - i)
    # show up to 3 to 7 numbers after the current number, depending on how many we already have
    for i in range(7 - len(show_pages)):
        if (page + i) <= paginator.num_pages:
            show_pages.append(page + i)

    return show_pages