# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.management import call_command

from django.core.urlresolvers import reverse

from django.db import connections

from django.test import Client

import simplejson

fixtures = ['test_data.json']

c = Client()

def unjson(data):
    return simplejson.loads(data.content)

def setup():
    for db in connections:
        if globals().has_key('fixtures'):
            call_command('loaddata', *globals()['fixtures'], **{'verbosity': 0, 'commit': False, 'database': db})

def test_010_test_follow():
    c.get(reverse('follow_debate', args=('1', 'x')))

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

