"""
DB utility functions
"""

# XXX this should be moved to its own module

from trac.db import DatabaseManager

class SQLHelper(object):

    def actions(self, cur):
        """do actions once you have execute the SQL"""
        return {}

    def return_values(self, **kw):
        """return values from the SQL"""

    def __call__(self, env, sql, *params):
        db = env.get_db_cnx()
        cur = db.cursor()
        _data = {}
        try:
            cur.execute(sql, params)
            _data = self.actions(cur)
            db.commit()
        except Exception, e:
            env.log.error("""There was a problem executing sql:%s
with parameters:%s
Exception:%s""" %(sql, params, e))
            db.rollback()
        try:
            db.close()
        except:
            pass
        return self.return_values(**_data)

execute_non_query = SQLHelper()

class SQLGetAll(SQLHelper):
    def actions(self, cur):
        return dict(data=cur.fetchall(), desc=cur.description) 

    def return_values(self, **kw):
        return (kw.get('desc'), kw.get('data'))

get_all = SQLGetAll()

def get_all_dict(env, sql, *params):
    """Executes the query and returns a Result Set"""
    desc, rows = get_all(env, sql, *params);
    if not desc:
        return []

    results = []
    for row in rows:
        row_dict = {}
        for field, col in zip(row, desc):
            row_dict[col[0]] = field
        results.append(row_dict)
    return results

class SQLGetFirstRow(SQLHelper):
    def actions(self, cur):
        return dict(data=cur.fetchone())
    def return_values(self, **kw):
        return kw.get('data')

get_first_row = SQLGetFirstRow()

def get_scalar(env, sql, col=0, *params):
    """
    Gets a single value (in the specified column) 
    from the result set of the query
    """
    data = get_first_row(env, sql, *params)
    if data:
        return data[col]

class SQLGetColumn(SQLHelper):
    def actions(self, cur):
        data = cur.fetchall()
        return dict(data=[datum[0] for datum in data])
    def return_values(self, **kw):
        return kw.get('data')
    def __call__(self, env, table, column, where=None):
        sql = "select %s from %s" % (column, table)
        if where:
            sql += " where %s" % where
        return SQLHelper.__call__(self, env, sql)

get_column = SQLGetColumn()


def create_table(env, table):
    """
    create a table given a component
    """

    db_connector, _ = DatabaseManager(env)._get_connector()
    stmts = db_connector.to_sql(table)
    for stmt in stmts:
        execute_non_query(env, stmt)
