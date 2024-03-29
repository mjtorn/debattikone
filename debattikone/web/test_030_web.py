# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.management import call_command

from django.core.urlresolvers import reverse

from django.contrib.auth import models as auth_models

from annoying.functions import get_object_or_None

from django.core import mail

from django.db import connections

from django.test import Client

from debattikone.web import models

from django_nose.assertions import *

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

    assert_ok(res)

    assert_form_error(res, 'login_form', 'l_username', 'Virheellinen käyttäjätunnus')

    assert_template_not_used(res, '666index.html')

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

    assert_redirects(res, reverse('index'))

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

    assert_redirects(res, reverse('debate', args=('1', 'x')))

    # 302 -> re-GET
    res = c.get(reverse('debate', args=('1', 'x')))
    assert_contains(res, 'fourth')

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
    assert_redirects(res, reverse('debate', args=(d2.id, d2.topic.slug)))

    # Only one message as the invite was done before box reset
    retval = len(mail.outbox)
    exp_retval = 1
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    # Accidentally try to participate again
    assert_redirects(res, reverse('debate', args=(d2.id, d2.topic.slug)))


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
    u2o = 'This is user2 opening the debate'
    data = {
        'message': u2o,
    }
    res = c.post(current_location, data)

    assert_redirects(res, current_location)

    ## Test d2 got correct table in db
    retval = d2.get_table(as_text=True)
    exp_retval = [['', u2o]]
    assert retval == exp_retval, 'Table mismatch'

    ## Test fail other opening
    data = {
        'message': 'This is user2 opening the debate again, should fail',
    }
    res = c.post(current_location, data)

    exp_retval = 200
    retval = res.status_code
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    assert 'Puheenvuoro on toisella osapuolella' in res.content, 'Failed to transfer turn?'

    # Database check
    exp_retval = 1
    retval = d2.debatemessage_set.count()
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    # Email check
    retval = len(mail.outbox)
    exp_retval = 2
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_200_fourth_creates_topic():
    new_topic_location = reverse('new_topic')

    res = c.get(new_topic_location)
    assert_ok(res)

    ## Apparently posting data = {} does not cause errors here?
    # First test title is broken
    data = {
        'summary': 'fourth created this trolololoo'
    }
    res = c.post(new_topic_location, data)

    assert_form_error(res, 'new_topic_form', 'title', 'Tämä tieto tarvitaan')

    # Then test summary is broken
    data = {
        'title': 'fourth created'
    }
    res = c.post(new_topic_location, data)

    assert_form_error(res, 'new_topic_form', 'summary', 'Tämä tieto tarvitaan')

    # Succeed
    data = {
        'title': 'fourth created',
        'summary': 'fourth created this trolololoo',
        'debate': 'yesplzkthxbai',
    }
    res = c.post(new_topic_location, data)
    assert_redirects(res, reverse('new_debate', args=('fourth-created',)))

def test_210_fourth_creates_debate():
    new_debate_location = reverse('new_debate', args=('fourth-created',))

    # Database hax :/
    topic = get_object_or_None(models.Topic, slug='fourth-created')
    assert topic is not None, 'Getting "fourth-created" failed'

    # Do not invite anyone
    data = {
        'topic': topic.id,
    }
    res = c.post(new_debate_location, data)
    assert_code(res, 302)

    # Now we know we're going places
    globals()['debate_location'] = res['Location']

def test_220_fourth_can_open_without_other_participant():
    debate_location = globals()['debate_location']
    del globals()['debate_location']

    data = {
        'message': 'I am fourth, I open my recently-created debate',
    }
    res = c.post(debate_location, data)
    assert_redirects(res, debate_location)

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

