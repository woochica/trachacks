# Default lpq database

from trac.db import Table, Column

__all__ = ['default_table', 'db_version']

db_version = 1
default_table = Table('tracforge_subscriptions', key='id')[
                    Column('id', auto_increment=True),
                    Column('env'),
                    Column('type'),
                    Column('direction'),]
