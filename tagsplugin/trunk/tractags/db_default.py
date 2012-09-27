#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.db import Table, Column, Index

schema_version = 3

## Database schema
#

schema = [
    Table('tags', key=('tagspace', 'name', 'tag'))[
        Column('tagspace'),
        Column('name'),
        Column('tag'),
        Index(['tagspace', 'name']),
        Index(['tagspace', 'tag']),
    ]
]

## Default database values
#

# (table, (column1, column2), ((row1col1, row1col2), (row2col1, row2col2)))
def get_data(db):
    return (('permission',
              ('username', 'action'),
                (('anonymous', 'TAGS_VIEW'),
                 ('authenticated', 'TAGS_EDIT'))),
            ('system',
              ('name', 'value'),
                (('tags_version', str(schema_version)),)))
