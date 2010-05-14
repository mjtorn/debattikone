# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.management import call_command

from django.core.urlresolvers import reverse

from django.contrib.auth import models as auth_models

from django.core import mail

from django.db import connections

from django.test import Client

from debattikone.web import models

import simplejson

#fixtures = ['test_data.json']

c = Client()

def unjson(data):
    return simplejson.loads(data.content)

def setup():
    for db in connections:
        if globals().has_key('fixtures'):
            call_command('loaddata', *globals()['fixtures'], **{'verbosity': 0, 'commit': False, 'database': db})

    # Fallia hella, fallia hella, fallia helle, fallia helle!
    mail.outbox = []

def test_010_fail_test_follow_no_login():
    data = c.get(reverse('follow_debate', args=('1', 'x')))
    data = unjson(data)

    assert not data['success'], 'Should fail, not logged in'
    assert data['msg'] == 'nologin', 'Should fail, not logged in'

def test_011_login_bad_fields():
    username = 'antagonist'
    password = 'test_case_password'

    data = {
        'username': username,
        'password': password,
    }

    res = c.post(reverse('index'), data)

    retval = res.status_code
    exp_retval = 200
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_012_login_bad_name():
    username = 'antagonist'
    password = 'test_case_password'

    data = {
        'l_username': username + '666',
        'l_password': password,
    }

    res = c.post(reverse('index'), data)

    retval = res.status_code
    exp_retval = 200
    assert retval == exp_retval, '%s != %s\n%s' % (retval, exp_retval, res.content)

def test_013_login_ok():
    """antagonist finally logs in
    """

    # Set here, not knowing a better place
    antagonist = auth_models.User.objects.get(username='antagonist')
    globals()['antagonist'] = antagonist

    username = 'antagonist'
    password = 'test_case_password'

    data = {
        'l_username': username,
        'l_password': password,
    }

    res = c.post(reverse('index'), data)

    retval = res.status_code
    exp_retval = 302
    assert retval == exp_retval, '%s != %s\n%s' % (retval, exp_retval, res.content)

def test_010_test_follow():
    """antagonist loads the front page, the first debate, and follows
    """

    c.get(reverse('index'))
    c.get(reverse('debate', args=('1', 'x')))

    data = c.get(reverse('follow_debate', args=('1', 'x')))
    data = unjson(data)

    assert data['success'], data
    assert data['msg'] == 'ok', data

def test_011_participate():
    """antagonist participates in the debate he was invited to
    """

    ## Get the correct debate here
    d = models.Debate.objects.filter(invited=antagonist).select_related(depth=1)[0]
    globals()['debate'] = d

    # Load page
    c.get(reverse('debate', args=(d.id, d.topic.slug)))

    # Participate
    res = c.get(reverse('participate', args=(d.id, d.topic.slug)))

    exp_retval = 302
    retval = res.status_code
    assert retval == exp_retval, '%s != %s\n%s' % (retval, exp_retval, res.content)

    # Only one message as the invite was done before box reset
    retval = len(mail.outbox)
    exp_retval = 1
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    # Accidentally try to participate again
    exp_retval = 302
    retval = res.status_code
    assert retval == exp_retval, '%s != %s\n%s' % (retval, exp_retval, res.content)


def test_012_open():
    """antagonist opens the debate
    """

    # Use this only to remember which page we're on
    current_location = reverse('debate', args=(debate.id, debate.topic.slug))

    res = c.get(current_location)

    exp_retval = 200
    retval = res.status_code
    assert retval == exp_retval, '%s != %s\n%s' % (retval, exp_retval, res.content)

    # Post opening
    data = {
        'message': 'This is user2 opening the debate',
    }
    res = c.post(current_location, data)

    exp_retval = 302
    retval = res.status_code
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    exp_retval = 1
    retval = debate.debatemessage_set.count()
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

