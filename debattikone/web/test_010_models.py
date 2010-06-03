# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import models as auth_models
from django.core.management import call_command

from django.db import connections

from debattikone.web import models

fixtures = ['test_data.json']

def setup():
    for db in connections:
        if globals().has_key('fixtures'):
            call_command('loaddata', *globals()['fixtures'], **{'verbosity': 0, 'commit': False, 'database': db})

    # >8D
    for a in dir(models):
        if a.startswith('TYPE'):
            globals()[a] = getattr(models, a)

def test_010_create_topic():
    topic = models.Topic()

    topic.title = 'Test debate'
    topic.summary = 'Summary for test debate'

    topic.save()

    globals()['topic'] = topic

def test_020_create_debate():
    mjt = auth_models.User.objects.get(username='mjt')

    debate = models.Debate()

    debate.topic = topic
    debate.user1 = mjt

    debate.save()

    globals()['debate'] = debate

def test_021_test_participate_mjt():
    mjt = auth_models.User.objects.get(username='mjt')

    can_participate = debate.can_participate(mjt)

    assert not can_participate, 'Test case knows you are user1 here'

def test_022_test_participate_and_participate_antagonist():
    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    can_participate = debate.can_participate(antagonist)

    assert can_participate, 'You are the other one, should be ok'

    debate.participate(antagonist)

    debate.save()

def test_023_test_participate_third():
    third = auth_models.User.objects.get(username='third')

    can_participate = debate.can_participate(third)

    assert not can_participate, 'Debate has two users'

def test_030_create_other_debate():
    mjt = auth_models.User.objects.get(username='mjt')

    topic = models.Topic()

    topic.title = 'Other test debate'
    topic.summary = 'Summary for other test debate'

    topic.save()

    globals()['other_topic'] = topic

    debate = models.Debate()

    debate.topic = topic
    debate.user1 = mjt

    debate.save()

    globals()['other_debate'] = debate

def test_031_fail_antagonist_inviting():
    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = other_debate.can_invite(antagonist, mjt)
    exp_retval = False
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_032_fail_inviting_self():
    mjt = auth_models.User.objects.get(username='mjt')

    retval = other_debate.can_invite(mjt, mjt)
    exp_retval = False
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_033_invite_antagonist():
    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = other_debate.can_invite(mjt, antagonist)
    exp_retval = True
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    other_debate.invite(antagonist)

def test_034_fail_third_participate():
    third = auth_models.User.objects.get(username='third')

    can_participate = other_debate.can_participate(third)
    assert not can_participate, 'antagonist was invited, not you'

def test_035_antagonist_participate():
    antagonist = auth_models.User.objects.get(username='antagonist')

    other_debate.participate(antagonist)

def test_040_create_duplicate_topic():
    topic = models.Topic()

    topic.title = 'Test debate'
    topic.summary = 'Summary for test debate'

    topic.save()

    globals()['topic'] = topic

def test_041_create_other_duplicate_topic():
    topic = models.Topic()

    topic.title = 'Test debate'
    topic.summary = 'Summary for test debate'

    topic.save()

    topic = topic

def test_050_housekeeping():
    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')
    third = auth_models.User.objects.get(username='third')

    count = models.Debate.objects.count()
    exp_count = 2
    assert count == exp_count, '%s != %s' % (count, exp_count)

    count = mjt.debate_user1_set.count()
    exp_count = 2
    assert count == exp_count, '%s != %s' % (count, exp_count)

    count = antagonist.debate_user2_set.count()
    exp_count = 2
    assert count == exp_count, '%s != %s' % (count, exp_count)

    count = antagonist.debate_invited_set.count()
    exp_count = 1
    assert count == exp_count, '%s != %s' % (count, exp_count)

    count = models.Topic.objects.count()
    exp_count = 4
    assert count == exp_count, '%s != %s' % (count, exp_count)

    print [t.slug for t in models.Topic.objects.all()]

def test_100_third_can_not_send():
    third = auth_models.User.objects.get(username='third')

    retval = debate.can_send(third)
    exp_retval = TYPE_NOTHING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_110_user2_tries_to_open():
    """user1 has not opened yet, so user2 can do it (test only can_send)
    """

    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = debate.can_send(antagonist)
    exp_retval = TYPE_OPEN
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_111_user1_opens():
    """user1 opens the debate
    """

    mjt = auth_models.User.objects.get(username='mjt')

    retval = debate.can_send(mjt)
    exp_retval = TYPE_OPEN
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    globals()['user1_open_arg'] = 'user1 opening argument'
    debate.send(mjt, retval, user1_open_arg)

    retval = debate.get_table()
    exp_retval = [[user1_open_arg, '']]
    assert retval == exp_retval, 'Table mismatch'

def test_112_user2_presents_open():
    """user2 presents his opening argument
    """

    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = debate.can_send(antagonist)
    exp_retval = TYPE_OPEN
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    globals()['user2_open_arg'] = 'user2 opening argument'
    debate.send(antagonist, retval, user2_open_arg)

    print [s.argument_type for s in debate.debatemessage_set.all()]

    retval = debate.get_table()
    exp_retval = [[user1_open_arg, user2_open_arg]]
    assert retval == exp_retval, 'Table mismatch'

    ## Also fail having antagonist trying to send
    retval = debate.can_send(antagonist)
    exp_retval = TYPE_NOTHING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_113_user1_first_q():
    """User 1 tests can_send, can send a normal argument
    and thus presents the first question
    """

    mjt = auth_models.User.objects.get(username='mjt')

    retval = debate.can_send(mjt)
    exp_retval = TYPE_QUESTION
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    globals()['u1q1'] = 'user1 first question'
    debate.send(mjt, retval, u1q1)

    retval = debate.get_table()
    exp_retval = [[user1_open_arg, user2_open_arg], [u1q1, '']]
    assert retval == exp_retval, 'Table mismatch'

def test_114_user2_first_re():
    """User 2 tests can_send, can send a normal, answers the
    question
    """

    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = debate.can_send(antagonist)
    exp_retval = TYPE_REPLY
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    globals()['u2r1'] = 'user2 first re'
    debate.send(antagonist, retval, u2r1)

    retval = debate.get_table()
    exp_retval = [[user1_open_arg, user2_open_arg], [u1q1, ''], ['', u2r1]]
    assert retval == exp_retval, 'Table mismatch, %s' % retval

def test_115_user1_out_of_turn():
    """User 1 tests can_send, sees can not send (user2's turn)
    and thus does not.
    """

    mjt = auth_models.User.objects.get(username='mjt')

    retval = debate.can_send(mjt)
    exp_retval = TYPE_NOTHING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_116_user2_first_q_and_user1_re():
    """user2 asks first question
    """

    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    msgs = list(debate.debatemessage_set.all().order_by('id'))

    # Finish first round
    retval = debate.can_send(antagonist)
    exp_retval = TYPE_QUESTION
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    globals()['u2q1'] = 'user2 first q'
    debate.send(antagonist, retval, u2q1)

    retval = debate.get_table()
    exp_retval = [[user1_open_arg, user2_open_arg], [u1q1, ''], ['', u2r1], ['', u2q1]]
    assert retval == exp_retval, 'Table mismatch'

    retval = debate.can_send(mjt)
    exp_retval = TYPE_REPLY
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    globals()['u1r1'] = 'user1 first re'
    debate.send(mjt, retval, u1r1)

    retval = debate.get_table()
    exp_retval = [[user1_open_arg, user2_open_arg], [u1q1, ''], ['', u2r1], ['', u2q1], [u1r1, '']]
    assert retval == exp_retval, 'Table mismatch'

    ## For the rest of the debate
    globals()['exp_state'] = retval

    ## Now we should have two questions and two answers
    messages = debate.debatemessage_set.all()
    normal_messages = [m for m in messages if m.argument_type in (1, 2)]
    assert len(normal_messages) == 4, '%d != 4 normals' % len(normal_messages)

def test_117_rest_of_the_debate():
    """Play out the rest of the debate, as we now know no one
    can speak out of turn
    """

    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    msg_limit = debate.msg_limit

    messages = debate.debatemessage_set.all()
    normal_messages = [m for m in messages if m.argument_type in (1, 2)]

    # Symbolize page loads
    i = 0
    while True:
        i += 1
        messages = debate.debatemessage_set.all()
        normal_messages = [m for m in messages if m.argument_type in (1, 2)]

        if len(normal_messages) >= msg_limit:
            break

        ## user1 asks question
        retval = debate.can_send(mjt)
        exp_retval = TYPE_QUESTION
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        debate.send(mjt, retval, 'user1 q')

        # To test
        exp_state.append(['user1 q', ''])

        retval = debate.get_table()
        assert retval == exp_state, 'Table mismatch, %s' % retval

        ## user2 replies
        retval = debate.can_send(antagonist)
        exp_retval = TYPE_REPLY
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        debate.send(antagonist, retval, 'user2 re')

        # User2's reply is edited in-place like
        exp_state.append(['', 'user2 re'])

        retval = debate.get_table()
        assert retval == exp_state, 'Table mismatch'

        ## asks question
        retval = debate.can_send(antagonist)
        exp_retval = TYPE_QUESTION
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        debate.send(antagonist, retval, 'user2 q')

        # Update state
        exp_state.append(['', 'user2 q'])

        retval = debate.get_table()
        assert retval == exp_state, 'Table mismatch'

        ## user1 replies
        retval = debate.can_send(mjt)
        exp_retval = TYPE_REPLY
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        debate.send(mjt, retval, 'user1 re')

        # Update state
        exp_state.append(['user1 re', ''])

        retval = debate.get_table()
        assert retval == exp_state, 'Table mismatch'

    messages = debate.debatemessage_set.all()
    count = len([m for m in messages if m.argument_type in (1, 2)])
    assert count == msg_limit, '%s != %s' % (count, msg_limit)

def test_118_finalize_debate():
    """Users present their closing arguments
    """

    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')
    
    ## Test both can close
    retval = debate.can_send(mjt)
    exp_retval = TYPE_CLOSING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    retval = debate.can_send(antagonist)
    exp_retval = TYPE_CLOSING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    ## User1 does so
    u1c = 'user1 closes'
    debate.send(mjt, TYPE_CLOSING, u1c)

    retval = debate.get_table()
    exp_state.append([u1c, ''])
    assert retval == exp_state, 'Table mismatch, %s' % retval

    # User1 tries again
    retval = debate.can_send(mjt)
    exp_retval = TYPE_NOTHING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    # Forcibly sends
    u1c = 'user1 closes'
    debate.send(mjt, TYPE_CLOSING, u1c)

    # Still a fail
    retval = debate.get_table()
    #exp_state.append([u1c, ''])
    assert retval == exp_state, 'Table mismatch, %s' % retval

    ## User2 closes
    u2c = 'user2 closes'
    debate.send(antagonist, TYPE_CLOSING, u2c)

    retval = debate.get_table()

    # Update the state
    exp_state[-1][1] = u2c
    assert retval == exp_state, 'Table mismatch, %s' % retval

    ## Make sure these are closed
    retval = debate.can_send(mjt)
    exp_retval = TYPE_NOTHING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    retval = debate.can_send(antagonist)
    exp_retval = TYPE_NOTHING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    third = auth_models.User.objects.get(username='third')

    retval = debate.can_send(third)
    exp_retval = TYPE_NOTHING
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_200_hax_other_debate():
    """This would never happen irl, but edit second debate's msg_limit
    """

    try:
        other_debate.msg_limit = 11
        raise AssertionError('Should be multiplier of 4')
    except ValueError, e:
        print 'Caught "%s"' % e

    other_debate.msg_limit = 12
    other_debate.save()

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

