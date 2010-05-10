from settings import *

DATABASES['default']['ENGINE'] = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASES['default']['NAME'] = ':memory:'             # Or path to database file if using sqlite3.

