# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.views.decorators.csrf import csrf_protect

from annoying.utils import HttpResponseReload

from debattikone.web import forms

from django.shortcuts import render_to_response
from django.template import RequestContext

# Decorators

def has_login(func):
    def wrap(*args, **kwargs):
        req_ctx = args[1]
        request = req_ctx['request']

        data = request.POST.copy() or None

        login_form = forms.LoginForm()
        if data is not None:
            if data.has_key('l_username') and data.has_key('l_password'):
                login_form = forms.LoginForm(data)
                if login_form.is_valid():
                    from django.contrib.auth import authenticate, login
                    username = login_form.cleaned_data['user'].username
                    password = login_form.cleaned_data['l_password']

                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)

                        return HttpResponseReload(request)
        req_ctx['login_form'] = login_form
        return func(*args, **kwargs)
    return wrap

render_login = has_login(render_to_response)

# Create your views here.

@csrf_protect
def index(request):
    context = {
        'title': 'Etusivu',
    }
    req_ctx = RequestContext(request, context)
    return render_login('index.html', req_ctx)

# EOF

