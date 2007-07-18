# DBSchema_version_1
from trac.db import Table, Column, Index, DatabaseManager

tables = [
    Table('mtp_suites', key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('title'),
        Column('description'),
        Column('component'),
        Column('deleted', type = 'integer'),
        Column('user')
    ],
    Table('mtp_suite_runs', key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('rDate', type = 'integer'),
        Column('status', type = 'integer'),
        Column('version'),
        Column('suite_id', type = 'integer'),
        Column('user')
    ],
    Table('mtp_plans', key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('suite_id', type = 'integer'),
        Column('cDate', type = 'integer'),
        Column('mDate', type = 'integer'),
        Column('title'),
        Column('description'),
        Column('priority'),
        Column('user')
    ],
    Table('mtp_plan_runs', key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('plan_id', type = 'integer'),
        Column('rDate', type = 'integer'),
        Column('status', type = 'integer'),
        Column('version'),
        Column('ticket', type = 'integer'),
        Column('user')
    ]
]

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()
    # Create tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)