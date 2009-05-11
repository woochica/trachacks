"""
utility functions
"""

from trac.db import DatabaseManager


def execute_non_query(com,  sql, *params):
    """Executes the query on the given project DB"""

    db = com.env.get_db_cnx()
    cur = db.cursor()
    try:
        cur.execute(sql, params)
        db.commit()
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \nwith parameters:%s\nException:%s' % (sql, params, e))
        db.rollback()
    try:
        db.close()
    except:
        pass


def get_first_row(com, sql, *params):
    """ 
    Returns the first row of the query results as a tuple of values (or None)
    """
    db = com.env.get_db_cnx()
    cur = db.cursor()
    data = None
    try:
        cur.execute(sql, params)
        data = cur.fetchone()
        db.commit()
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \nwith parameters:%s\nException:%s'%(sql, params, e))
        db.rollback()
    try:
        db.close()
    except:
        pass
    return data

def get_column(com, table, column):
    """
    Return the column of name as a list
    """

    db = com.env.get_db_cnx()
    cur = db.cursor()
    sql = "select %s from %s" % (column, table)
    try:
        cur.execute(sql)
        data = cur.fetchall()
    except Exception, e:
        com.log.error('There was a problem executing sql:%s\nException:%s'%(sql, e))
        db.rollback()
    try:
        db.close()
    except:
        pass
    data = [datum[0] for datum in data]
    return data

def get_scalar(com, sql, col=0, *params):
    """
    Gets a single value (in the specified column) 
    from the result set of the query
    """
    data = get_first_row(com, sql, *params)
    if data:
        return data[col]
    else:
        return None


def create_table(comp, table):
    """
    create a table given a component
    """

    db_connector, _ = DatabaseManager(comp.env)._get_connector()
    
    stmts = db_connector.to_sql(table)
    for stmt in stmts:
        execute_non_query(comp, stmt)
