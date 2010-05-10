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
