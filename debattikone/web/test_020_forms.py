# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.management import call_command

from django.contrib.auth import models as auth_models

from debattikone.web import forms, models

from django.db import connections

def setup():
    for db in connections:
        if globals().has_key('fixtures'):
            call_command('loaddata', *globals()['fixtures'], **{'verbosity': 0, 'commit': False, 'database': db})

def test_010_invalid_email():
    data = {
        'username': 'mjt',
        'email': 'mjt',
        'password': 'test_case_password',
    }

    form = forms.RegisterForm(data)
    assert not form.is_valid()
    print form.errors

def test_011_invalid_name():
    data = {
        'username': 'mjt' * 12,
        'email': 'mjt@nysv.org',
        'password': 'test_case_password',
    }

    form = forms.RegisterForm(data)
    assert not form.is_valid()
    print form.errors

def test_012_no_password():
    data = {
        'username': 'mjt' * 12,
        'email': 'mjt@nysv.org',
    }

    form = forms.RegisterForm(data)
    assert not form.is_valid()
    print form.errors

def test_013_duplicate_mjt():
    data = {
        'username': 'mjt',
        'email': 'mjt@nysv.org',
        'password': 'test_case_password',
    }

    form = forms.RegisterForm(data)
    assert not form.is_valid()
    print form.errors

def test_014_reg_antagonist():
    data = {
        'username': 'antagonist',
        'email': 'mjt+debatti@nysv.org',
        'password': 'test_case_password',
    }

    form = forms.RegisterForm(data)
    assert form.is_valid(), form.errors
    form.save()

def test_015_reg_third():
    data = {
        'username': 'third',
        'email': 'mjt+debatti@nysv.org',
        'password': 'test_case_password',
    }

    form = forms.RegisterForm(data)
    assert form.is_valid(), form.errors
    form.save()

def test_100_fail_new_topic():
    data = {
        'title': 'a' * 65,
        'summary': 'First summary',
    }

    form = forms.NewTopicForm(data)
    assert not form.is_valid(), 'Should fail'

def test_101_fail_new_topic_summary():
    data = {
        'title': 'First topic',
        'summary': 'a' * 1065
    }

    form = forms.NewTopicForm(data)
    assert not form.is_valid(), 'Should fail'

def test_102_fail_new_topic_no_summary():
    data = {
        'title': 'First topic',
    }

    form = forms.NewTopicForm(data)
    assert not form.is_valid(), 'Should fail'

def test_103_success_new_topic():
    data = {
        'title': 'First topic',
        'summary': 'First summary',
    }

    form = forms.NewTopicForm(data)
    assert form.is_valid(), form.errors
    form.save()

def test_104_success_dupe_topic():
    data = {
        'title': 'First topic',
        'summary': 'First summary',
    }

    form = forms.NewTopicForm(data)
    assert form.is_valid(), form.errors
    form.save()

def test_200_fail_new_debate_topic():
    topics = models.Topic.objects.all().order_by('-id')
    topic = topics[0]
    topic_id = topic.id + 1

    mjt = auth_models.User.objects.get(username='mjt')

    globals()['topic'] = topic
    globals()['mjt'] = mjt

    data = {
        'topic': topic_id,
    }
    form = forms.NewDebateForm(data)
    assert not form.is_valid(), 'Should fail'
    print form.errors

def test_201_success_new_debate_no_invite():
    data = {
        'topic': topic.id,
    }

    form = forms.NewDebateForm(data)
    form.data['request_user'] = mjt
    assert form.is_valid(), form.errors
    form.cleaned_data['user'] = mjt
    form.save()

def test_201_fail_duplicate_debate_no_invite():
    data = {
        'topic': topic.id,
    }

    form = forms.NewDebateForm(data)
    form.data['request_user'] = mjt
    assert not form.is_valid(), 'Should fail'
    print form.errors

def test_202_success_new_debate_invite():
    antagonist = auth_models.User.objects.get(username='antagonist')
    globals()['antagonist'] = antagonist

    data = {
        'topic': topic.id,
        'invited': antagonist.id,
    }

    form = forms.NewDebateForm(data)
    form.data['request_user'] = mjt
    assert form.is_valid(), form.errors
    form.cleaned_data['user'] = mjt
    globals()['invite_debate'] = form.save()

    exp_retval = 2
    retval = models.Debate.objects.count()
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_203_success_new_debate_invite_random():
    data = {
        'topic': topic.id,
        'invite_random': True,
        'user': mjt,
    }

    form = forms.NewDebateForm(data)
    form.data['request_user'] = mjt
    assert form.is_valid(), form.errors
    form.cleaned_data['user'] = mjt
    form.save()

    del form

def test_204_fail_new_debate_no_more_randoms():
    data = {
        'topic': topic.id,
        'invite_random': True,
        'user': mjt,
    }

    form = forms.NewDebateForm(data)
    form.data['request_user'] = mjt
    assert not form.is_valid(), 'Should have no more randoms'

## Until we have good view tests
#def teardown():
#    for db in connections:
#        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

