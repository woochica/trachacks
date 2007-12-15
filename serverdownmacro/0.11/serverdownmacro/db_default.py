# Created by Noah Kantrowitz on 2007-12-15.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.db import Table, Column

name = 'serverdown'
version = 1
tables = [
    Table('serverdown', key=('host', 'port'))[
        Column('host'),
        Column('port'),
        Column('ts'),
        Column('value'),
    ],
]