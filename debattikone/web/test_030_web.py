# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.management import call_command

from django.core.urlresolvers import reverse

from django.db import connections

from django.test import Client

import simplejson

#fixtures = ['test_data.json']

c = Client()

def unjson(data):
    return simplejson.loads(data.content)

def setup():
    for db in connections:
        if globals().has_key('fixtures'):
            call_command('loaddata', *globals()['fixtures'], **{'verbosity': 0, 'commit': False, 'database': db})

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
    data = c.get(reverse('follow_debate', args=('1', 'x')))
    data = unjson(data)

    assert data['success'], data
    assert data['msg'] == 'ok', data

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

