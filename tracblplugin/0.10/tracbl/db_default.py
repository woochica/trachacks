# Database schema for TracBL
from trac.db.schema import Table, Column

name = 'tracbl_database'
version = 1
tables = [
    # Table to hold the API keys as they are generated
    Table('tracbl_apikeys', 'id')[
        Column('id', auto_increment=True),
        Column('key'),
        Column('email'),
    ],
    
    # Table to track hostname submissions
    Table('tracbl_hosts', 'id')[
        Column('id'),
        Column('host'),
        Column('user'),
    ],
    
]
        
