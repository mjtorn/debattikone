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

    def test_022_test_participate_and_join_antagonist(self):
        mjt = auth_models.User.objects.get(username='mjt')
        antagonist = auth_models.User.objects.get(username='antagonist')

        can_participate = self.State.debate.can_participate(antagonist)

        assert can_participate, 'You are the other one, should be ok'

        self.State.debate.join(antagonist)

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

        try:
            self.State.other_debate.invite(antagonist, mjt)
            raise AssertionError('Should have failed')
        except models.DebattikoneInvalidUserException, e:
            print 'Caught %s' % e

    def test_032_fail_inviting_self(self):
        mjt = auth_models.User.objects.get(username='mjt')

        try:
            self.State.other_debate.invite(mjt, mjt)
            raise AssertionError('Should have failed')
        except models.DebattikoneInvalidUserException, e:
            print 'Caught %s' % e

    def test_033_invite_antagonist(self):
        mjt = auth_models.User.objects.get(username='mjt')
        antagonist = auth_models.User.objects.get(username='antagonist')

        self.State.other_debate.invite(mjt, antagonist)

    def test_034_fail_third_join(self):
        third = auth_models.User.objects.get(username='third')

        can_participate = self.State.other_debate.can_participate(third)
        assert not can_participate, 'antagonist was invited, not you'

        try:
            self.State.other_debate.join(third)
            raise AssertionError('You were not invited')
        except models.DebattikoneInvalidUserException, e:
            print 'Caught %s' % e

    def test_035_antagonist_join(self):
        antagonist = auth_models.User.objects.get(username='antagonist')

        self.State.other_debate.join(antagonist)

    def test_040_housekeeping(self):
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

# EOF

