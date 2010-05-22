# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from settings import DATABASES

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Markus Törnqvist', 'mjt@fadconsulting.com'),
)

TIME_ZONE = 'Europe/Helsinki'
LANGUAGE_CODE = 'fi'

DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
DATABASES['default']['NAME'] = '/home/mjt/tmp/debattikone.db'

TEST_RUNNER = 'django_nose.run_tests'

# EOF

