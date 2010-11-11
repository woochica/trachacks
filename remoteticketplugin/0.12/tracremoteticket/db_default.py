from trac.db import Table, Column, Index

__all__ = ['name', 'version', 'schema']

name = 'remote_tickets'
version = 1

schema  = [
    Table(name, key=('source_name', 'source', 
                     'destination_name', 'destination'))[
        Column('source_name'),
        Column('source', type='int'),
        Column('destination_name', type='string'),
        Column('destination'),
        Column('type'),
        Column('cachetime', type='int64'),
        Column('c_summary'),
        Column('c_status'),
        Column('c_type'),
        Column('c_resolution'),
        Index(['cachetime']),
        Index(['c_status']),
        ],
    ]
