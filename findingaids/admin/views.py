from django.shortcuts import render_to_response
from django.http import Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.template import RequestContext
from findingaids.admin.models import Login
import os
import glob
from datetime import datetime
from django.conf import settings
from eulcore.django.existdb.db import ExistDB

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
                            'error' : error },
                            context_instance=RequestContext(request))

def admin_login(request):
    "Admin page"
    return render_to_response('admin/index.html', context_instance=RequestContext(request))

def publish(request):
    "Publish an EAD file from configured source directory so it is visible on the site."
    if request.method == 'POST':
        filename = request.POST['filename']
        print filename
        fullpath = os.path.join(settings.FINDINGAID_EAD_SOURCE, filename)
        db = ExistDB()
        # load the document to the configured collection in eXist with the same fileneame
        # FIXME: allow overwrite on first try ? notify user if it is a new file or an update ?
        success = db.load(open(fullpath), settings.EXISTDB_ROOT_COLLECTION + "/" + filename, True)
        return render_to_response('admin/publish.html',
                                    {'success' : success, 'filename' : filename },
                                    context_instance=RequestContext(request))
    else:
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
