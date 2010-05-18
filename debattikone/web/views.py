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
        register_form = forms.RegisterForm()
        if data is not None:
            l_username = data.get('l_username')
            l_password = data.get('l_password')
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            if l_username and l_password:
                login_form = forms.LoginForm(data)
                if login_form.is_valid():
                    from django.contrib.auth import authenticate, login
                    username = login_form.cleaned_data['user'].username
                    password = login_form.cleaned_data['l_password']

                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)

                        return HttpResponseReload(request)
            elif username and password and email:
                register_form = forms.RegisterForm(data)
                if register_form.is_valid():
                    from django.contrib.auth import authenticate, login
                    register_form.save()

                    user = authenticate(username=username, password=password)
                    login(request, user)

                    return HttpResponseReload(request)

        req_ctx['login_form'] = login_form
        req_ctx['register_form'] = register_form
        return func(*args, **kwargs)
    return wrap

render_login = has_login(render_to_response)

# Create your views here.

def logout_view(request):
    from django.contrib.auth import logout
    next = request.GET.get('next', '/')

    logout(request)

    return HttpResponseRedirect(next)

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
            topic = new_topic_form.save()

            if data.get('debate'):
                return HttpResponseRedirect(reverse('new_debate', args=(topic.slug,)))
            else:
                return HttpResponseReload(request)


    context = {
        'new_topic_form': new_topic_form,
        'title': 'Uusi keskustelunaihe',
    }
    req_ctx = RequestContext(request, context)
    return render_login('new_topic.html', req_ctx)

@csrf_protect
def new_debate(request, slug=None):
    if slug:
        topic = get_object_or_404(models.Topic, slug=slug)

    data = request.POST.copy() or None

    if slug:
        initial = {
            'topic': topic.id,
        }
    else:
        initial = None

    new_debate_form = forms.NewDebateForm(data=data, initial=initial)

    if new_debate_form.is_bound:
        if new_debate_form.is_valid():
            new_debate_form.cleaned_data['user'] = request.user
            debate = new_debate_form.save()

            return HttpResponseRedirect(reverse('debate', args=(debate.id, topic.slug)))

    context = {
        'new_debate_form': new_debate_form,
        'title': 'Uusi debatti',
    }
    req_ctx = RequestContext(request, context)
    return render_login('new_debate.html', req_ctx)

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

