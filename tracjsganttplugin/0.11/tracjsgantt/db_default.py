from trac.db import Table, Column, Index

# The TracPM environment
name = 'TracPM'
# Version 1 is the current schedule and history
version = 1

# The schedule table holds the current calculated start and finish for
# each ticket
tables = [
     Table('schedule', key=('ticket')) [
         Column('ticket', type='int'),
         Column('start', type='int64'),
         Column('finish', type='int64'),
         Index(['ticket']),
     ],
     Table('schedule_change', key=('ticket', 'time')) [
         Column('ticket', type='int'),
         Column('time', type='int64'),
         Column('oldstart', type='int64'),
         Column('oldfinish', type='int64'),
         Column('newstart', type='int64'),
         Column('newfinish', type='int64'),
         Index(['ticket']),
         Index(['time']),
     ],
    ]

