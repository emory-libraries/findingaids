import os
import glob
from datetime import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login
from django.contrib import messages


from eulcore.django.existdb.db import ExistDB
from eulcore.xmlmap.core import load_xmlobject_from_file

from findingaids.fa.models import FindingAid
from findingaids.admin.utils import check_ead


@login_required
def main(request):
    """
    Main admin page.

    List recently modified files in configured source directory to be previewed
    or published.
    """
    recent_files = []
    if not hasattr(settings, 'FINDINGAID_EAD_SOURCE'):
        error = "Please configure EAD source directory in local settings."
    else:
        dir = settings.FINDINGAID_EAD_SOURCE
        if os.access(dir, os.F_OK | os.R_OK):
            recent_files = _get_recent_xml_files(dir)
            error = None
        else:
            error = "EAD source directory '%s' does not exist or is not readable; please check config file." % dir
        
    return render_to_response('admin/index.html', {'files' : recent_files,
                            'error' : error},
                            context_instance=RequestContext(request))


def admin_logout(request):
    """
    Admin Login page.

    
    """
    login_url = settings.LOGIN_URL
    messages.success(request, 'You have logged out of finding aids.')
    return logout_then_login(request)



@login_required
def publish(request):
    """
    Admin publication form.

    On POST, publish the EAD file specified in request from the configured
    source directory to make it immediately visible on the site.

    On GET, display a list of files available for publication.
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


def _get_recent_xml_files(dir, num=30):
    "Return recently modified xml files from the specified directory."
    # get all xml files in the specified directory
    filenames = glob.glob(os.path.join(dir, '*.xml'))
    # modified time, base name of the file
    files = [ (os.path.getmtime(file), os.path.basename(file)) for file in filenames ]
    # reverse sort - most recently modified first
    files.sort(reverse=True)
    # convert modified time into a datetime object (only process and return the requested number)
    recent_files = [ (filename, datetime.utcfromtimestamp(mtime)) for mtime, filename in files[0:num] ]
    return recent_files
