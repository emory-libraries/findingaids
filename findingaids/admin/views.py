from django.shortcuts import render_to_response
from django.http import Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.template import RequestContext
from findingaids.admin.models import Login

def admin_login(request):
    "Admin page"
    return render_to_response('admin/index.html', context_instance=RequestContext(request))
