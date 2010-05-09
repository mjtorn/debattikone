# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import models as auth_models

from debattikone.web import models

from django.test import TestCase

from nose.util import try_run

class StatefulTestCase(TestCase):
    class State:
        pass

    def setUp(self):
        names = ('setup',)
        try_run(self, names)

    def tearDown(self):
        names = ('teardown',)
        try_run(self, names)

    def _fixture_setup(self):
        """Set up transaction management, but skip real reset
        """

        from django.core.management import call_command
        from django.test.testcases import connections_support_transactions
        from django.test.testcases import disable_transaction_methods
        from django.db import transaction, connections, DEFAULT_DB_ALIAS

        if not connections_support_transactions():
            return super(TestCase, self)._fixture_setup()

        # If the test case has a multi_db=True flag, setup all databases.
        # Otherwise, just use default.
        if getattr(self, 'multi_db', False):
            databases = connections
        else:
            databases = [DEFAULT_DB_ALIAS]

        for db in databases:
            transaction.enter_transaction_management(using=db)
            transaction.managed(True, using=db)
        disable_transaction_methods()

        from django.contrib.sites.models import Site
        Site.objects.clear_cache()

        for db in databases:
            if hasattr(self, 'fixtures'):
                call_command('loaddata', *self.fixtures, **{'verbosity': 0, 'commit': False, 'database': db})

    def _fixture_teardown(self):
        """Must not tear down recent commits, or it's not stateful!
        """

        return None

class Test010Models(StatefulTestCase):
    fixtures = ['test_data.json']

    def test_010_create_topic(self):
        topic = models.Topic()

        topic.title = 'Test debate'
        topic.summary = 'Summary for test debate'

        topic.save()

        self.State.topic = topic

    def test_020_create_debate(self):
        mjt = auth_models.User.objects.get(username='mjt')

        debate = models.Debate()

        debate.topic = self.State.topic
        debate.user1 = mjt

        debate.save()

        self.State.debate = debate

    def test_021_test_participate_mjt(self):
        mjt = auth_models.User.objects.get(username='mjt')

        can_participate = self.State.debate.can_participate(mjt)

        assert not can_participate, 'Test case knows you are user1 here'

    def test_022_test_participate_and_participate_antagonist(self):
        mjt = auth_models.User.objects.get(username='mjt')
        antagonist = auth_models.User.objects.get(username='antagonist')

        can_participate = self.State.debate.can_participate(antagonist)

        assert can_participate, 'You are the other one, should be ok'

        self.State.debate.participate(antagonist)

        self.State.debate.save()

    def test_023_test_participate_third(self):
        third = auth_models.User.objects.get(username='third')

        can_participate = self.State.debate.can_participate(third)

        assert not can_participate, 'Debate has two users'

    def test_030_create_other_debate(self):
        mjt = auth_models.User.objects.get(username='mjt')

        topic = models.Topic()

        topic.title = 'Other test debate'
        topic.summary = 'Summary for other test debate'

        topic.save()

        self.State.other_topic = topic

        debate = models.Debate()

        debate.topic = topic
        debate.user1 = mjt

        debate.save()

        self.State.other_debate = debate

    def test_031_fail_antagonist_inviting(self):
        mjt = auth_models.User.objects.get(username='mjt')
        antagonist = auth_models.User.objects.get(username='antagonist')

        retval = self.State.other_debate.can_invite(antagonist, mjt)
        exp_retval = False
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    def test_032_fail_inviting_self(self):
        mjt = auth_models.User.objects.get(username='mjt')

        retval = self.State.other_debate.can_invite(mjt, mjt)
        exp_retval = False
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    def test_033_invite_antagonist(self):
        mjt = auth_models.User.objects.get(username='mjt')
        antagonist = auth_models.User.objects.get(username='antagonist')

        retval = self.State.other_debate.can_invite(mjt, antagonist)
        exp_retval = True
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        self.State.other_debate.invite(antagonist)

    def test_034_fail_third_participate(self):
        third = auth_models.User.objects.get(username='third')

        can_participate = self.State.other_debate.can_participate(third)
        assert not can_participate, 'antagonist was invited, not you'

    def test_035_antagonist_participate(self):
        antagonist = auth_models.User.objects.get(username='antagonist')

        self.State.other_debate.participate(antagonist)

    def test_040_create_duplicate_topic(self):
        topic = models.Topic()

        topic.title = 'Test debate'
        topic.summary = 'Summary for test debate'

        topic.save()

        self.State.topic = topic

    def test_041_create_other_duplicate_topic(self):
        topic = models.Topic()

        topic.title = 'Test debate'
        topic.summary = 'Summary for test debate'

        topic.save()

        self.State.topic = topic

    def test_050_housekeeping(self):
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

    def test_100_third_can_not_send(self):
        third = auth_models.User.objects.get(username='third')

        retval = self.State.debate.can_send(third)
        exp_retval = None
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    def test_110_user2_tries_to_open(self):
        """user1 has not opened the debate yet, so user2's can_send
        must return None
        """

        antagonist = auth_models.User.objects.get(username='antagonist')

        retval = self.State.debate.can_send(antagonist)
        exp_retval = None
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    def test_111_user1_opens(self):
        """user1 opens the debate
        """

        mjt = auth_models.User.objects.get(username='mjt')

        retval = self.State.debate.can_send(mjt)
        exp_retval = 0
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        self.State.debate.send(mjt, retval, 'user1 opening argument')

    def test_112_user2_presents_open(self):
        """user2 presents his opening argument
        """

        antagonist = auth_models.User.objects.get(username='antagonist')

        retval = self.State.debate.can_send(antagonist)
        exp_retval = 0
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        self.State.debate.send(antagonist, retval, 'user2 opening argument')

        print [s.argument_type for s in self.State.debate.debatemessage_set.all()]

    def test_113_user1_first_q(self):
        """User 1 tests can_send, can send a normal argument
        and thus presents the first question
        """

        mjt = auth_models.User.objects.get(username='mjt')

        retval = self.State.debate.can_send(mjt)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        self.State.debate.send(mjt, retval, 'user1 first question')

    def test_114_user2_first_re(self):
        """User 2 tests can_send, can send a normal, answers the
        question
        """

        antagonist = auth_models.User.objects.get(username='antagonist')

        retval = self.State.debate.can_send(antagonist)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        self.State.debate.send(antagonist, retval, 'user2 first re')

    def test_115_user1_out_of_turn(self):
        """User 1 tests can_send, sees can not send (user2's turn)
        and thus does not.
        """

        mjt = auth_models.User.objects.get(username='mjt')

        retval = self.State.debate.can_send(mjt)
        exp_retval = None
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

    def test_116_user2_first_q_and_user1_re(self):
        """user2 asks first question
        """

        mjt = auth_models.User.objects.get(username='mjt')
        antagonist = auth_models.User.objects.get(username='antagonist')

        # Finish first round
        retval = self.State.debate.can_send(antagonist)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        self.State.debate.send(antagonist, retval, 'user2 first q')

        retval = self.State.debate.can_send(mjt)
        exp_retval = 1
        assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

        self.State.debate.send(mjt, retval, 'user1 first re')

        ## Now we should have two questions and two answers
        messages = self.State.debate.debatemessage_set.all()
        normal_messages = [m for m in messages if m.argument_type == 1]
        assert len(normal_messages) == 4, '%d != 4 normals' % len(normal_messages)

    def test_117_rest_of_the_debate(self):
        """Play out the rest of the debate, as we now know no one
        can speak out of turn
        """

        mjt = auth_models.User.objects.get(username='mjt')
        antagonist = auth_models.User.objects.get(username='antagonist')

        msg_limit = self.State.debate.msg_limit

        messages = self.State.debate.debatemessage_set.all()
        normal_messages = [m for m in messages if m.argument_type == 1]

        # Symbolize page loads
        i = 0
        while True:
            i += 1
            messages = self.State.debate.debatemessage_set.all()
            normal_messages = [m for m in messages if m.argument_type == 1]

            if len(normal_messages) >= msg_limit:
                break

            # user1 asks question
            retval = self.State.debate.can_send(mjt)
            exp_retval = 1
            assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

            self.State.debate.send(mjt, retval, 'user1 q')

            # user2 replies
            retval = self.State.debate.can_send(antagonist)
            exp_retval = 1
            assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

            self.State.debate.send(antagonist, retval, 'user2 re')

            # asks question
            retval = self.State.debate.can_send(antagonist)
            exp_retval = 1
            assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

            self.State.debate.send(antagonist, retval, 'user2 q')

            # user1 replies
            retval = self.State.debate.can_send(mjt)
            exp_retval = 1
            assert retval == exp_retval, '%s != %s' % (retval, exp_retval)

            self.State.debate.send(mjt, retval, 'user1 re')

        messages = self.State.debate.debatemessage_set.all()
        count = len([m for m in messages if m.argument_type == 1])
        assert count == msg_limit, '%s != %s' % (count, msg_limit)

# EOF

