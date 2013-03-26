# Created by Noah Kantrowitz on 2007-04-02.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.db import Table, Column

name = 'hidevals'
version = 1
tables = [
    Table('hidevals', key=('sid', 'field', 'value'))[
        Column('sid'),
        Column('field'),
        Column('value'),
    ],   
]