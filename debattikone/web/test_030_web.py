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

def test_014_logout_ok():
    """antagonist logs out
    """

    c.get(reverse('logout'))

def test_015_register_new():
    """a new participant browses and registers
    """

    c.get(reverse('index'))

    # See the complete list of debates
    c.get(reverse('debate_list'))

    # See the list of open debates
    c.get(reverse('debate_list', kwargs={'filter': 'open'}))

    # Open one
    c.get(reverse('debate', args=('1', 'x')))

    # "See" the login/register forms and register
    data = {
        'username': 'fourth',
        'password': 'test_case_password',
        'email': 'mjt+debattikone@nysv.org',
    }

    res = c.post(reverse('debate', args=('1', 'x')), data)

    globals()['user2'] = auth_models.User.objects.get(username='fourth')

    exp_retval = 302
    retval = res.status_code
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_110_test_follow():
    """antagonist loads the front page, the first debate, and follows
    """

    c.get(reverse('index'))
    c.get(reverse('debate', args=('1', 'x')))

    data = c.get(reverse('follow_debate', args=('1', 'x')))
    data = unjson(data)

    assert data['success'], data
    assert data['msg'] == 'ok', data

    # Semi-hacky
    c.get(reverse('debate', args=('2', 'x')))

    data = c.get(reverse('follow_debate', args=('2', 'x')))
    data = unjson(data)

    assert data['success'], data


def test_111_participate():
    """'fourth' tries to participate in wrong debate, participates in ok
    """

    ## Get the correct debates here
    antagonist_invited = models.Debate.objects.filter(invited=antagonist).select_related(depth=1)[0]
    antagonist_not_invited = models.Debate.objects.exclude(invited=antagonist).select_related(depth=1)[0]
    globals()['d'] = antagonist_invited
    globals()['d2'] = antagonist_not_invited

    # Load page
    c.get(reverse('debate', args=(d.id, d.topic.slug)))

    # Participate in wrong debate
    res = c.get(reverse('participate', args=(d.id, d.topic.slug)))

    exp_retval = None
    retval = d.user2
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    # Load page
    c.get(reverse('debate', args=(d2.id, d2.topic.slug)))

    # Participate in correct
    res = c.get(reverse('participate', args=(d2.id, d2.topic.slug)))

    # Check that we set the user ok
    antagonist_not_invited = models.Debate.objects.exclude(invited=antagonist).select_related(depth=1)[0]
    globals()['d2'] = antagonist_not_invited
    exp_retval = user2
    retval = d2.user2
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    # and redireced out
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


def test_112_open():
    """antagonist opens the debate
    """

    # Use this only to remember which page we're on
    current_location = reverse('debate', args=(d2.id, d2.topic.slug))

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
    assert retval == exp_retval, '%s != %s\n%s' % (retval, exp_retval, res.content)

    # Database check
    exp_retval = 1
    retval = d2.debatemessage_set.count()
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    # Email check
    retval = len(mail.outbox)
    exp_retval = 2
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

