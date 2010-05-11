# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import models as auth_models
from django.core.management import call_command

from django.db import connections

from debattikone.web import models

fixtures = ['test_data.json']

class State:
    pass

def setup():
    for db in connections:
        if globals().has_key('fixtures'):
            call_command('loaddata', *globals()['fixtures'], **{'verbosity': 0, 'commit': False, 'database': db})

def test_010_create_topic():
    topic = models.Topic()

    topic.title = 'Test debate'
    topic.summary = 'Summary for test debate'

    topic.save()

    State.topic = topic

def test_020_create_debate():
    mjt = auth_models.User.objects.get(username='mjt')

    debate = models.Debate()

    debate.topic = State.topic
    debate.user1 = mjt

    debate.save()

    State.debate = debate

def test_021_test_participate_mjt():
    mjt = auth_models.User.objects.get(username='mjt')

    can_participate = State.debate.can_participate(mjt)

    assert not can_participate, 'Test case knows you are user1 here'

def test_022_test_participate_and_participate_antagonist():
    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    can_participate = State.debate.can_participate(antagonist)

    assert can_participate, 'You are the other one, should be ok'

    State.debate.participate(antagonist)

    State.debate.save()

def test_023_test_participate_third():
    third = auth_models.User.objects.get(username='third')

    can_participate = State.debate.can_participate(third)

    assert not can_participate, 'Debate has two users'

def test_030_create_other_debate():
    mjt = auth_models.User.objects.get(username='mjt')

    topic = models.Topic()

    topic.title = 'Other test debate'
    topic.summary = 'Summary for other test debate'

    topic.save()

    State.other_topic = topic

    debate = models.Debate()

    debate.topic = topic
    debate.user1 = mjt

    debate.save()

    State.other_debate = debate

def test_031_fail_antagonist_inviting():
    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = State.other_debate.can_invite(antagonist, mjt)
    exp_retval = False
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_032_fail_inviting_self():
    mjt = auth_models.User.objects.get(username='mjt')

    retval = State.other_debate.can_invite(mjt, mjt)
    exp_retval = False
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_033_invite_antagonist():
    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = State.other_debate.can_invite(mjt, antagonist)
    exp_retval = True
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    State.other_debate.invite(antagonist)

def test_034_fail_third_participate():
    third = auth_models.User.objects.get(username='third')

    can_participate = State.other_debate.can_participate(third)
    assert not can_participate, 'antagonist was invited, not you'

def test_035_antagonist_participate():
    antagonist = auth_models.User.objects.get(username='antagonist')

    State.other_debate.participate(antagonist)

def test_040_create_duplicate_topic():
    topic = models.Topic()

    topic.title = 'Test debate'
    topic.summary = 'Summary for test debate'

    topic.save()

    State.topic = topic

def test_041_create_other_duplicate_topic():
    topic = models.Topic()

    topic.title = 'Test debate'
    topic.summary = 'Summary for test debate'

    topic.save()

    State.topic = topic

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

    retval = State.debate.can_send(third)
    exp_retval = None
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_110_user2_tries_to_open():
    """user1 has not opened the debate yet, so user2's can_send
    must return None
    """

    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = State.debate.can_send(antagonist)
    exp_retval = None
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_111_user1_opens():
    """user1 opens the debate
    """

    mjt = auth_models.User.objects.get(username='mjt')

    retval = State.debate.can_send(mjt)
    exp_retval = 0
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    State.debate.send(mjt, retval, 'user1 opening argument')

def test_112_user2_presents_open():
    """user2 presents his opening argument
    """

    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = State.debate.can_send(antagonist)
    exp_retval = 0
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    State.debate.send(antagonist, retval, 'user2 opening argument')

    print [s.argument_type for s in State.debate.debatemessage_set.all()]

def test_113_user1_first_q():
    """User 1 tests can_send, can send a normal argument
    and thus presents the first question
    """

    mjt = auth_models.User.objects.get(username='mjt')

    retval = State.debate.can_send(mjt)
    exp_retval = 1
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    State.debate.send(mjt, retval, 'user1 first question')

def test_114_user2_first_re():
    """User 2 tests can_send, can send a normal, answers the
    question
    """

    antagonist = auth_models.User.objects.get(username='antagonist')

    retval = State.debate.can_send(antagonist)
    exp_retval = 1
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    State.debate.send(antagonist, retval, 'user2 first re')

def test_115_user1_out_of_turn():
    """User 1 tests can_send, sees can not send (user2's turn)
    and thus does not.
    """

    mjt = auth_models.User.objects.get(username='mjt')

    retval = State.debate.can_send(mjt)
    exp_retval = None
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

def test_116_user2_first_q_and_user1_re():
    """user2 asks first question
    """

    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    # Finish first round
    retval = State.debate.can_send(antagonist)
    exp_retval = 1
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    State.debate.send(antagonist, retval, 'user2 first q')

    retval = State.debate.can_send(mjt)
    exp_retval = 1
    assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    State.debate.send(mjt, retval, 'user1 first re')

    ## Now we should have two questions and two answers
    messages = State.debate.debatemessage_set.all()
    normal_messages = [m for m in messages if m.argument_type == 1]
    assert len(normal_messages) == 4, '%d != 4 normals' % len(normal_messages)

def test_117_rest_of_the_debate():
    """Play out the rest of the debate, as we now know no one
    can speak out of turn
    """

    mjt = auth_models.User.objects.get(username='mjt')
    antagonist = auth_models.User.objects.get(username='antagonist')

    msg_limit = State.debate.msg_limit

    messages = State.debate.debatemessage_set.all()
    normal_messages = [m for m in messages if m.argument_type == 1]

    # Symbolize page loads
    i = 0
    while True:
        i += 1
        messages = State.debate.debatemessage_set.all()
        normal_messages = [m for m in messages if m.argument_type == 1]

        if len(normal_messages) >= msg_limit:
            break

        # user1 asks question
        retval = State.debate.can_send(mjt)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        State.debate.send(mjt, retval, 'user1 q')

        # user2 replies
        retval = State.debate.can_send(antagonist)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        State.debate.send(antagonist, retval, 'user2 re')

        # asks question
        retval = State.debate.can_send(antagonist)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        State.debate.send(antagonist, retval, 'user2 q')

        # user1 replies
        retval = State.debate.can_send(mjt)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        State.debate.send(mjt, retval, 'user1 re')

    messages = State.debate.debatemessage_set.all()
    count = len([m for m in messages if m.argument_type == 1])
    assert count == msg_limit, '%s != %s' % (count, msg_limit)

def test_200_hax_other_debate():
    """This would never happen irl, but edit second debate's msg_limit
    """

    try:
        State.other_debate.msg_limit = 11
        raise AssertionError('Should be multiplier of 4')
    except ValueError, e:
        print 'Caught "%s"' % e

    State.other_debate.msg_limit = 12
    State.other_debate.save()

def teardown():
    for db in connections:
        call_command('flush', verbosity=0, interactive=False, database=db)

# EOF

