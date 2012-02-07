import trac.db.sqlite_backend
import trac.db.postgres_backend
import trac.db.mysql_backend

def get_all(env, sql, *params):
    """Executes the query and returns the (description, data)"""
    db = env.get_read_db()
    cur = db.cursor()
    desc  = None
    data = None
    try:
        cur.execute(sql, params)
        data = list(cur.fetchall())
        desc = cur.description
    except Exception, e:
        env.log.exception('There was a problem executing sql:%s \n \
with parameters:%s\nException:%s'%(sql, params, e));
   
    return (desc, data)

def execute_non_query(env, sql, *params):
    """Executes the query on the given project"""
    execute_in_trans(env, (sql, params))
   
def get_first_row(env, sql,*params):
    """ Returns the first row of the query results as a tuple of values (or None)"""
    db = env.get_read_db()
    cur = db.cursor()
    data = None;
    try:
        cur.execute(sql, params)
        data = cur.fetchone();
    except Exception, e:
        env.log.exception('There was a problem executing sql:%s \n \
        with parameters:%s\nException:%s'%(sql, params, e));
    return data;

def get_scalar(env, sql, col=0, *params):
    """ Gets a single value (in the specified column) from the result set of the query"""
    data = get_first_row(env, sql, *params);
    if data:
        return data[col]
    else:
        return None;

def execute_in_trans(env, *args):
    result = True
    c_sql =[None]
    c_params = [None]
    try:
        @env.with_transaction()
        def fn(db):
            cur = db.cursor()
            for sql, params in args:
                c_sql[0] = sql
                c_params[0] = params
                cur.execute(sql, params)
    except Exception, e :
        env.log.exception('There was a problem executing sql:%s \n \
    with parameters:%s\nException:%s'%(c_sql[0], c_params[0], e));
        raise e
    return result

def execute_in_nested_trans(env, name, *args):
    result = True
    c_sql =[None]
    c_params = [None]
    @env.with_transaction()
    def fn(db):
        cur = None
        try:
            cur = db.cursor()
            cur.execute("SAVEPOINT %s" % name)
            for sql, params in args:
                c_sql[0] = sql
                c_params[0] = params
                cur.execute(sql, params)
            cur.execute("RELEASE SAVEPOINT %s" % name)
        except Exception, e :
            cur.execute("ROLLBACK TO SAVEPOINT %s" % name)
            env.log.exception('There was a problem executing sql:%s \n \
    with parameters:%s\nException:%s'%(c_sql[0], c_params[0], e));
            raise e
    return result

def current_schema (env):
    db = env.get_read_db()
    if (type(db.cnx) == trac.db.sqlite_backend.SQLiteConnection):
        return None
    elif (type(db.cnx) == trac.db.mysql_backend.MySQLConnection):
        return get_scalar(env, 'SELECT schema();')
    elif (type(db.cnx) == trac.db.postgres_backend.PostgreSQLConnection):
        return get_scalar(env, 'SHOW search_path;')

def _prep_schema(s):
    return ','.join(("'"+i.replace("'","''")+"'"
                     for i in s.split(',')))

def db_table_exists(env,  table):
    db = env.get_read_db()
    cnt = None
    if(type(db.cnx) == trac.db.sqlite_backend.SQLiteConnection):
        sql = "select count(*) from sqlite_master where type = 'table' and name = %s"
        cnt = get_scalar(env, sql, 0, table)
    else:
        sql = """SELECT count(*) FROM information_schema.tables 
                 WHERE table_name = %%s and table_schema in (%s)
              """ % _prep_schema(current_schema(env))
        print sql
        cnt = get_scalar(env, sql, 0, table)
    return cnt > 0

def get_column_as_list(env, sql, col=0, *params):
    data = get_all(env, sql, *params)[1] or ()
    return [valueList[col] for valueList in data]

def get_system_value(env, key):
    return get_scalar(env, "SELECT value FROM system WHERE name=%s", 0, key)

def set_system_value(env, key, value):
    if get_system_value(env, key):
        execute_non_query(env, "UPDATE system SET value=%s WHERE name=%s", value, key)        
    else:
        execute_non_query(env, "INSERT INTO system (value, name) VALUES (%s, %s)",
            value, key)


def get_result_set(env, sql, *params):
    """Executes the query and returns a Result Set"""
    tpl = get_all(env, sql, *params);
    if tpl and tpl[0] and tpl[1]:
        return ResultSet(tpl)
    else:
        return None


class ResultSet:
    """ the result of calling getResultSet """
    def __init__ (self, (columnDescription, rows)):
        self.columnDescription, self.rows = columnDescription, rows 
        self.columnMap = self.get_column_map()

    def get_column_map ( self ):
        """This function will take the result set from getAll and will
        return a hash of the column names to their index """
        h = {}
        i = 0
        if self.columnDescription:
            for col in self.columnDescription:
                h[ col[0] ] = i
                i+=1
        return h;
    
    def value(self, col, row ):
        """ given a row(list or idx) and a column( name or idx ), retrieve the appropriate value"""
        tcol = type(col)
        trow = type(row)
        if tcol == str:
            if(trow == list or trow == tuple):
                return row[self.columnMap[col]]
            elif(trow == int):
                return self.rows[row][self.columnMap[col]]
            else:
                print ("rs.value Type Failed col:%s  row:%s" % (type(col), type(row)))
        elif tcol == int:
            if(trow == list or trow == tuple):
                return row[col]
            elif(trow == int):
                return self.rows[row][col]
            else:
                print ("rs.value Type Failed col:%s  row:%s" % (type(col), type(row)))
        else:
            print ("rs.value Type Failed col:%s  row:%s" % (type(col), type(row)))
   
    def json_out(self):
        json = "[%s]" % ',\r\n'. join(
            [("{%s}" % ','.join(
            ["'%s':'%s'" %
             (key, unicode(self.value(val, row)).
              replace("'","\\'").
              replace('"','\\"').
              replace('\r','\\r').
              replace('\n','\\n'))
             for (key, val) in self.columnMap.items()]))
             for row in self.rows])
        #mylog.debug('serializing to json : %s'% json)
        return json
