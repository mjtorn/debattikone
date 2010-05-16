# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.views.decorators.csrf import csrf_protect

from django.core.urlresolvers import reverse

from annoying.utils import HttpResponseReload

from debattikone.web import forms, models

from django.http import HttpResponseRedirect

from django.shortcuts import render_to_response, get_object_or_404
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
    ## Feature a random debate
    try:
        debate = models.Debate.objects.all().order_by('?')[0]
    except IndexError:
        debate = 'kala' #None

    context = {
        'debate': debate,
        'title': 'Etusivu',
    }
    req_ctx = RequestContext(request, context)
    return render_login('index.html', req_ctx)

@csrf_protect
def new_topic(request):
    data = request.POST.copy() or None

    new_topic_form = forms.NewTopicForm(data)

    if new_topic_form.is_bound:
        if new_topic_form.is_valid():
            new_topic_form.save()

            if data.get('debate'):
                return HttpResponseRedirect(reverse('new_debate'))
            else:
                return HttpResponseReload(request)


    context = {
        'new_topic_form': new_topic_form,
        'title': 'Uusi keskustelunaihe',
    }
    req_ctx = RequestContext(request, context)
    return render_login('new_topic.html', req_ctx)

def debate(request, debate_id, slug):
    debate = get_object_or_404(models.Debate, id=debate_id)

    data = request.POST.copy() or None

    debate_message_form = forms.DebateMessageForm(data)
    if debate_message_form.is_bound:
        debate_message_form.data['debate'] = debate
        debate_message_form.data['user'] = request.user

        if debate_message_form.is_valid():
            debate_message_form.save()

            return HttpResponseReload(request)
        # For debug purposes
        else:
            print debate_message_form.errors

    context = {
    }
    req_ctx = RequestContext(request, context)
    return render_login('debate.html', req_ctx)

def participate(request, debate_id, slug):
    debate = get_object_or_404(models.Debate, id=debate_id)

    can_participate = debate.can_participate(request.user)
    if can_participate:
        debate.participate(request.user)

    return HttpResponseRedirect(reverse('debate', args=(debate_id, slug)))


# EOF

