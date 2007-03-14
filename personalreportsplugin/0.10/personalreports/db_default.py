from trac.db import Table, Column

name = 'personalreports'
version = 1
tables = [
    Table('personal_reports', key=('id', 'user'))[
        Column('id'),
        Column('user'),
        Column('private'),
        Column('title'),
        Column('query'),
        Column('description'),
    ],
]