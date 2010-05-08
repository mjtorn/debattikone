# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.test import TestCase

class StatefulTestCase(TestCase):
    def _fixture_setup(self):
        """Set up transaction management, but skip real reset
        """

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


# EOF
