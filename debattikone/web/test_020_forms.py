# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.management import call_command

from debattikone.web import forms

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

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

