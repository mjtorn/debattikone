# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from annoying.decorators import render_to
from django.template import RequestContext

# Create your views here.

@render_to('index.html')
def index(request):
    context = {
        'title': 'Etusivu',
    }
    return context

# EOF

