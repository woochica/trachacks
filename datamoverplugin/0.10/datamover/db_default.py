# Database schema for Datamover
from trac.db.schema import Table, Column

name = 'datamover_database'
version = 1
tables = [
    Table('datamover_envs', 'env')[
        Column('env'),
    ],
]
