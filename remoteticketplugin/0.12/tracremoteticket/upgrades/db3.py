from trac.db import DatabaseManager

from tracremoteticket.db_default import schema

def do_upgrade(env, ver, cursor):
    """Replace remote tickets table with one having all fields of ticket table  (as of Trac 0.13dev).
    """
    remote_tickets = [t for t in schema if t.name == 'remote_tickets'][0]
    db_connector, _ = DatabaseManager(env)._get_connector()
    statements = ['DROP TABLE remote_tickets']
    statements.extend(db_connector.to_sql(remote_tickets))
    for stmt in statements:
        cursor.execute(stmt)
