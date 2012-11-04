from trac.db import Table, Column, Index, DatabaseManager

schema = [
    Table('subscription', key='id')[
        Column('id', auto_increment=True),
        Column('time', type='int64'),
        Column('changetime', type='int64'),
        Column('class'),
        Column('sid'),
        Column('authenticated', type='int'),
        Column('distributor'),
        Column('format'),
        Column('priority', type='int'),
        Column('adverb')
    ],
    Table('subscription_attribute', key='id')[
        Column('id', auto_increment=True),
        Column('sid'),
        Column('class'),
        Column('realm'),
        Column('target')
    ]
]

def do_upgrade(env, ver, cursor):
    """Migrate old `subscriptions` db table.

    Changes to other tables:
    'subscription.priority' type=(default == char) --> 'int'
    'subscription_attribute.name --> 'subscription_attribute.realm'
    'subscription_attribute.value --> 'subscription_attribute.target'
    """
    cursor.execute("""
        CREATE TEMPORARY TABLE subscription_old
            AS SELECT * FROM subscription
    """)
    cursor.execute("DROP TABLE subscription")
    cursor.execute("""
        CREATE TEMPORARY TABLE subscription_attribute_old
            AS SELECT * FROM subscription_attribute
    """)
    cursor.execute("DROP TABLE subscription_attribute")

    connector = DatabaseManager(env)._get_connector()[0]
    for table in schema:
        for stmt in connector.to_sql(table):
            cursor.execute(stmt)
    db = env.get_db_cnx()
    # Convert priority values to integer.
    cursor.execute("""
        INSERT INTO subscription
               (time,changetime,class,sid,authenticated,
                distributor,format,priority,adverb)
        SELECT o.time,o.changetime,o.class,o.sid,o.authenticated,
               o.distributor,o.format,%s,o.adverb
          FROM subscription_old AS o
        """ % db.cast('o.priority', 'int'))
    cursor.execute("DROP TABLE subscription_old")

    # Copy table on column name change.
    cursor.execute("""
        INSERT INTO subscription_attribute
               (sid,class,realm,target)
        SELECT o.sid,o.class,o.name,o.value
          FROM subscription_attribute_old AS o
    """)
    cursor.execute("DROP TABLE subscription_attribute_old")

    # DEVEL: Migrate old subscription db table data.
    cursor.execute("DROP TABLE IF EXISTS subscriptions")
