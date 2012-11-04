from trac.db import Table, Column, Index, DatabaseManager

schema = [
    Table('subscription_attribute', key='id')[
        Column('id', auto_increment=True),
        Column('sid'),
        Column('authenticated', type='int'),
        Column('class'),
        Column('realm'),
        Column('target')
    ]
]

def do_upgrade(env, ver, cursor):
    """Change `subscription_attribute` db table:

    + 'subscription_attribute.authenticated'
    """
    cursor.execute("""
        CREATE TEMPORARY TABLE subscription_attribute_old
            AS SELECT * FROM subscription_attribute
    """)
    cursor.execute("DROP TABLE subscription_attribute")

    connector = DatabaseManager(env)._get_connector()[0]
    for table in schema:
        for stmt in connector.to_sql(table):
            cursor.execute(stmt)
    cursor.execute("""
        INSERT INTO subscription_attribute
               (sid,authenticated,class,realm,target)
        SELECT o.sid,s.authenticated,o.class,o.realm,o.target
          FROM subscription_attribute_old AS o
          LEFT JOIN session AS s
               ON o.sid=s.sid
    """)
    cursor.execute("DROP TABLE subscription_attribute_old")

    # DEVEL: Think that an old 'subscriptions' db table may still exist here.
    cursor.execute("DROP TABLE IF EXISTS subscriptions")
