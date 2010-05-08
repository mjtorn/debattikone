# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import models as auth_models

from debattikone.web import models

from django.core import mail
from django.test import TestCase

from nose.util import try_run

class StatefulTestCase(TestCase):
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

class Test010Models(StatefulTestCase):
    fixtures = ['test_data.json']

    def test_010_create_topic(self):
        topic = models.Topic()

        topic.title = 'Test debate'
        topic.summary = 'Summary for test debate'

        topic.save()

        self.topic = topic

# EOF

