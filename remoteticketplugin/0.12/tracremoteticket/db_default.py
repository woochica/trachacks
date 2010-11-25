from trac.db import Table, Column, Index

__all__ = ['version', 'schema']

name = 'remote_ticket'
version = 3

schema  = [
    Table('remote_ticket_links', 
          key=('source_name', 'source', 'type',
               'destination_name', 'destination'))[
        Column('source_name'),
        Column('source', type='int'),
        Column('type'),
        Column('destination_name'),
        Column('destination', type='int'),
        ],
    Table('remote_tickets', key=('remote_name', 'id'))[
        Column('remote_name'),
        Column('id', type='int'),
        Column('cachetime', type='int64'),
        Column('time', type='int64'),
        Column('changetime', type='int64'),
        Column('component'),
        Column('severity'),
        Column('priority'),
        Column('owner'),
        Column('reporter'),
        Column('cc'),
        Column('version'),
        Column('milestone'),
        Column('status'),
        Column('resolution'),
        Column('summary'),
        Column('description'),
        Column('keywords'),
        Index(['cachetime']),
        Index(['status']),
        ],
    ]
