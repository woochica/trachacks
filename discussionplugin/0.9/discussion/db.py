from trac.core import *
from trac.db_default import Table, Column, Index

# Version of discussion schema
version = 1

schema = [
    Table('forum', key=('id', 'name'))[
        Column('id', type='int', auto_increment = True),
        Column('name'),
        Column('time', type='int'),
        Column('moderators'),
        Column('subject'),
        Column('description')],
    Table('topic', key = 'id')[
        Column('id', type='int', auto_increment = True),
        Column('forum', type='int'),
        Column('time', type='int'),
        Column('author'),
        Column('subject'),
        Column('body')],
    Table('message', key = 'id')[
        Column('id', type='int', auto_increment = True),
        Column('forum', type='int'),
        Column('topic', type='int'),
        Column('replyto', type='int'),
        Column('time', type='int'),
        Column('author'),
        Column('body')],
]
