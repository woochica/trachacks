from trac.db import DatabaseManager
from coderev.model import CodeReview

def do_upgrade(env, cursor):
    
    # create the initial tables (and indexes)
    db_connector = DatabaseManager(env).get_connector()[0]
    for table in CodeReview.db_tables:
        for sql in db_connector.to_sql(table):
            cursor.execute(sql)
