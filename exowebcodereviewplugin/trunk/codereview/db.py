# db.py

from trac.db import Table, Column

version = 1

schema = [
       Table('codereview', key = ('id', 'version'))[
         Column('id', type = 'int'),
         Column('author'),
         Column('status', type = 'int'),
         Column('time', type = 'int'),
         Column('text'),
         Column('version', type='int'),
         Column('priority')],
       Table('REV_PATH', key = ('rev',))[
         Column('rev'),
         Column('path')],
         ]
