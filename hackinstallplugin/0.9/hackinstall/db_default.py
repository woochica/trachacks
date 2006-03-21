from trac.db import Table, Column

__all__ = ['default_hacks_table']

default_hacks_table = Table('hacks', key='id')[
                    Column('id', auto_increment=True),
                    Column('name'),
                    Column('current'),
                    Column('description'),
                    Column('deps')]
