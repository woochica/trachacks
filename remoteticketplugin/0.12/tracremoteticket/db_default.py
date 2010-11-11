from trac.db import Table, Column, Index

__all__ = ['version', 'schema']

name = 'remote_ticket'
version = 2

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
        Column('summary'),
        Column('status'),
        Column('type'),
        Column('resolution'),
        Index(['cachetime']),
        Index(['status']),
        ],
    ]
