

def get_all(db, sql, *params):
    """Executes the query and returns the (description, data)"""
    cur = db.cursor()
    try:
        cur.execute(sql, params)
        data = cur.fetchall()
        desc = cur.description

    finally:
        cur.close()
        db.close()
    return (desc, data)

def execute_non_query(con, sql, *params):
    """Executes the query on the given project"""
    cur = con.cursor()
    try:
        cur.execute(sql, params)
        con.commit()
    finally:
        cur.close()
        con.close()

def get_database_table_names(db):
    sql =" SELECT tbl_name FROM SQLITE_MASTER WHERE type='table' "
    return get_column_as_list(db, sql);

def get_scalar(db, sql, col=0, *params):
    cur = db.cursor()
    try:
        cur.execute(sql, params)
        data = cur.fetchone()
    finally:
        cur.close()
        db.close()
    return data[col]

def get_column_as_list(db, sql, col=0, *params):
    return [valueList[col] for valueList in get_all(db, sql, *params)[1]]


def get_result_set(db, sql, *params):
    """Executes the query and returns a Result Set"""
    return ResultSet(get_all(db, sql, *params))

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
   
