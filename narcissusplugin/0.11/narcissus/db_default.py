#
# Narcissus plugin for Trac
#
# Copyright (C) 2008 Kim Upton	
# All rights reserved.	
#

from trac.core import *
from trac.db.schema import Table, Column, Index

# Version number used to determine if upgrade is required
version = 1

# Tables for the Narcissus plugin
tables = [
    Table('narcissus_settings', key=('type', 'value'))[
    	# effectively a dictionary of settings, it's extremely simple
        Column('type'),		# example: member, resource, bounds
        Column('value'),	# example: kupt2870, wiki, 300
    ],
    Table('narcissus_data')[
        Column('member'),	# the group member who made the change
        Column('dtime', type='int'),	# date time of the change
        Column('eid'),		# the changed item (wiki page, ticket, revision, etc)
        Column('resource'),	# the resource on which the change was made
        Column('type'),		# nature of the change (add, edit, update, comment, etc)
        Column('value', type='int'),	# the value associated with the change, eg. lines added
    ],
    Table('narcissus_bounds', key=('resource', 'level'))[
        Column('resource'),
        Column('level', type='int'),	# bound levels 1-3 for each resource
        Column('threshold', type='int'),
    ],
    Table('narcissus_credits', key='type')[
        Column('type'),
        Column('credit', type='int'),
    ],
]
