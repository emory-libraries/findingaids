from findingaids.admin.models import Login

def admin_login(request):
    "Admin page"
    return render_to_response('admin/index.html', context_instance=RequestContext(request))
