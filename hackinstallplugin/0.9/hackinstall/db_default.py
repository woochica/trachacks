from trac.db import Table, Column

__all__ = ['default_table']

default_table = Table('hacks', key='id')[
                    Column('id', auto_increment=True),
                    Column('name'),
                    Column('type'),
                    Column('current')]
