from django.contrib.flatpages.views import flatpage

def simplepage(request, url):
    # Just a wrapper for the normal flatpage view.
    return flatpage(request, url)