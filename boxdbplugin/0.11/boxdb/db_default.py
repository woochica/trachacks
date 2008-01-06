# Created by  on 2007-12-20.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.db import Table, Column

name = 'boxdb'
version = 2
tables = [
    Table('boxdb', key=('name', 'key'))[
        Column('name'),
        Column('key'),
        Column('value'), # JSON encoded
    ],
    Table('boxdb_changes', key=())[
        Column('document'), 
        Column('time'),
        Column('author'),
        Column('key'),
        Column('oldvalue'),
        Column('newvalue'),
    ],
]