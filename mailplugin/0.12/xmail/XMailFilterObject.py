'''
Created on 15.07.2010

@author: franz.mayer
'''

import re
import time

from trac.db.schema import Table, Column, Index
from trac.db.api import DatabaseManager
from trac.util.datefmt import parse_date,to_utimestamp, format_datetime,to_datetime
import math

#===============================================================================
# idea:
# maybe use a view for abstraction; then it is not needed to regex about SQL-Where clause 
#===============================================================================

# xmail table object
# see trac/db_default.py for samples and trac/db/schema.py for implementation of objects 
XMAIL_TABLE = Table('xmail', key='id')[
        Column('id', auto_increment=True),
        Column('filtername'),
        Column('username'),
        Column('nextexe', type='int64'),
        Column('lastsuccessexe', type='int64'),
        Column('selectfields', type='text'),
        Column('whereclause', type='text'),
        Column('interval', type='int'),
        Column('active', type='int'),
        Index(['filtername','username'],True),
        #Column('change'),
        ]

#===============================================================================
# Create Table xmail
#===============================================================================
def create_table(env):
    '''
    Constructor, see trac/db/postgres_backend.py:95 (method init_db)
    '''
    conn, dummyArgs = DatabaseManager(env).get_connector()
    db = env.get_read_db()
    cursor = db.cursor()

    for stmt in conn.to_sql(XMAIL_TABLE):
        if db.schema:
            stmt = re.sub(r'CREATE TABLE ','CREATE TABLE "' 
                          + db.schema + '".', stmt) 
        env.log.info( "result of execution: %s" % cursor.execute(stmt) )
    db.commit()
    db.close()

#===============================================================================
# Escaping
#===============================================================================
def encode_sql(sql_string):
    if sql_string:
        sql_string = sql_string.replace("'", "\\'")
        sql_string = sql_string.replace("\n", " ")
        sql_string = sql_string.replace("\t", " ")
        sql_string = sql_string.replace("\r", " ")
        sql_string = sql_string.replace("  ", " ")
        return sql_string
    
#===============================================================================
# Returns a list of the table columns
#===============================================================================
def get_col_list(ignore_cols=None):
    """ return col list as string; usable for selecting all cols 
    from xmail table """
    col_list = "";
    i = 0
    for col in XMAIL_TABLE.columns:
        try:
            if ignore_cols and ignore_cols.index(col.name) > -1: continue
        except: pass
        
        if (i > 0):
            col_list += ","
        col_list += col.name
        i += 1
    return col_list

#===============================================================================
# FilterObject to interpret http request, an offer an couple of helper methods
#===============================================================================
class FilterObject(object):
    '''
    classdocs
    implementation follows example of Ticket 
    (see trac/ticket/model.py:36 and following)
    '''   
    
    values = {}
    must_fields = ['filtername', 'username', 'interval']
    id = None
    name = None
    select_fields = None
    
    def __init__(self, req_or_id, db=None):
        if not req_or_id: 
            return
        if type(req_or_id) == int:
            if db:
                self.load_filter(db, req_or_id)
            return
        self.parse_request(req_or_id)
        
    def parse_request(self, req):
        self.username = req.authname
        for col in XMAIL_TABLE.columns:
            argVal = req.args.get(col.name)
            if argVal and col.name == "id" and not isinstance(argVal, int):
                continue
            elif col.name == "selectfields" and isinstance(argVal, (tuple, list)):
                self.select_fields = argVal
                argVal = self.get_select_fields_string(argVal)
            self.values[col.name] = argVal 


    def check_filter(self):
        is_ok = True
        for field in self.must_fields:
            is_ok &= self.values[field] is not None and len(self.values[field]) > 0
        return is_ok
    
    def getEmptyFields(self):
        emptyFields = []
        for field in self.must_fields:
            if self.values[field] is None or len(self.values[field]) < 1:
                emptyFields.append(field)
        return emptyFields
    
        
    def get_select_fields_string(self, sel_fields_list):
        if sel_fields_list is not None and isinstance(sel_fields_list, (list,tuple)):
            return ','.join(sel_fields_list)
        else:
            return str(sel_fields_list)

        
    def format_time(self, time_in_sec, always_return=True):
        """ if time_in_sec is None it will return current time 
        
        @param always_return: indicates if always a valid date/time should be returned"""
        if time_in_sec is None and always_return:
            # set default edit time 3 minutes after showing edit view
            time_in_sec = long(math.ceil(time.time()) + 180)
        if not time_in_sec is None and isinstance(time_in_sec,(long,int)):
            return format_datetime(time_in_sec)
        else:
            return time_in_sec
#        return format_datetime(time_in_sec, format='%d.%m.%Y %H:%M:%S')
        
    def get_select_fields_list(self, sel_fields_string):
        if sel_fields_string:
            self.select_fields = sel_fields_string.split(',')
            return self.select_fields
    
    #===========================================================================
    # getter of filter fields
    #===========================================================================
    def get_select_field(self, sel_field_str):
        try:
            idx = self.select_fields.index(sel_field_str)
            return self.select_fields[idx]
        except:
            return None
    
    #==================================================================
    # database and db-utils methods 
    #==================================================================    
    def load_filter(self, db, id):
        cursor = db.cursor()
        try:
            sql = ("select " + get_col_list() + " from " + XMAIL_TABLE.name 
                        + " where id=%s" % id)
            cursor.execute(sql)
            result = cursor.fetchone()
            self.id = id
            
            for i, col in enumerate(XMAIL_TABLE.columns):
                if col.name == "selectfields":
                    self.select_fields = self.get_select_fields_list(result[i])
                elif col.name == "filtername":
                    self.name = result[i]
                        
                if col.name == "whereclause":
                    self.values[col.name] = self._replace_sql_where_clause(result[i], True)
                else:    
                    self.values[col.name] = result[i]
                    
        except Exception, e:
            raise Exception( "Xmail exception: ", e)
    
    def get_filter_select(self, selectfields=None, whereclause=None, additional_where_clause=None):
        if not selectfields:
            selectfields = self.values['selectfields']
            if not selectfields:
                selectfields = "*"
                            
        if not whereclause:
            whereclause = self.values['whereclause']
            if not whereclause and not additional_where_clause:
                return "select id,%s from ticket" % selectfields
            elif not whereclause and additional_where_clause:
                return "select id,%s from ticket where %s" % (selectfields, additional_where_clause)
        
        if additional_where_clause:
            whereclause = "(%s) and (%s)" % (additional_where_clause, whereclause)
            
        if re.search("priority", whereclause):
            selectfields = re.sub(',', ',t.', selectfields)
            return "select t.id,%s from ticket t, enum e where %s" % (selectfields, whereclause)
        
        return "select id,%s from ticket where %s" % (selectfields, whereclause)
        
    def get_filter_select_from_db(self, db, id):
        cursor = db.cursor()
        sqlResult = {}
        try:
            sql = ("select nextexe, interval, selectfields,"
                   " whereclause from %s  where id=%s")%(XMAIL_TABLE.name,id)
            
            cursor.execute(sql)
            sqlResult = list(cursor.fetchall())

            if sqlResult and len(sqlResult) >0:
                 # take just first row, nothing else
                sqlResult = sqlResult[0]
                if len(sqlResult) > 2 :
                    sql_filter = self.get_filter_select(sqlResult[2],  sqlResult[3])

        except Exception, e:
            raise Exception(e, "Error executing SQL Statement \n ( %s ) " % (sql))
        return sql_filter
    
    def get_result(self, db, filter_sql, fetch_size=100):
        cursor = db.cursor()
        sqlResult = {}
        sqlHeaders = {}
        try:
            if fetch_size and filter_sql:
                filter_sql = "%s LIMIT %s" % (filter_sql, fetch_size)
            
            cursor.execute(filter_sql)
            sqlResult = list(cursor.fetchall())
            sqlHeaders = cursor.description
        except Exception, e:
            raise Exception(filter_sql,e)
        
        return sqlResult, sqlHeaders
        
    def _replace_sql_where_clause(self, where_clause, reverse=False):
        if where_clause:
            #self.log.debug("DEBUG: XMailFilterObject._replace_sql_where_clause: where_clause = %s" % where_clause) 
            self.log("DEBUG: XMailFilterObject._replace_sql_where_clause: where_clause = %s" % where_clause)
            replacements = {"(priority[\\s]*)([<>=]{1,2}[\\s]*'[\\d]{1,2}')": 
                            r"t.priority = e.name and e.type='priority' and e.value \2"}
            
            if reverse == True:
                replacements = {"(t.priority = e.name and e.type='priority' and e.value )([<>=]{1,2}[\\s]*'[\\d]{1,2}')":
                                r"priority \2"}
            for repl in replacements.keys():
                where_clause = re.sub(repl, replacements[repl], where_clause)
            self.log("DEBUG: XMailFilterObject._replace_sql_where_clause: where_clause = %s" % where_clause)
            return where_clause
            
    def save(self, db, update=False, id=None):
        sql = ""
        
        if update and not id:
            raise Exception("NO SQL", "ERROR: when updating field 'ID' is required.")
        elif update:
            sql += "UPDATE %s SET " % XMAIL_TABLE.name
        else:
            sql = "INSERT INTO %s (%s) VALUES (" % ( XMAIL_TABLE.name, get_col_list(['id']) )
        
        i = 0
        sel_fields = None
        where_clause = None
        
        for col in XMAIL_TABLE.columns:
            if col.name == "id":
                # ignore id -- will be generated
                continue
            val = self.values[col.name]
            
            if i > 0:
                sql += ","
            if update:
                sql += "%s=" % col.name
            
            if val:
                if col.name == "selectfields":
                    val = self.get_select_fields_string(val)
                    if val is not None or len(val)>0:
                        sql += "'" + encode_sql(val) + "'"
                    else:
                        val= "*"
                    sel_fields = val
                elif col.name == "whereclause":
                    val = self._replace_sql_where_clause(val)
                    where_clause = val
                    self.log("DEBUG: XMailFilterObject.save: where_clause = %s" % where_clause)                   
                    sql += "'" + encode_sql(val) + "'"
                elif col.type == "int64":
                    # val is datetime
                    
                    if isinstance(val, int):
                        val_date = str(val)
                    else:
                        val_date = str(to_utimestamp(parse_date(val)))
                    sql += val_date
                elif col.type == "text":
                    # encode sql, since it might have sign "'"
                    sql += "'" + encode_sql(val) + "'"
                else:
                    # ints and other types, which do not need any further work
                    sql += str(val)
                    
#                if col.name == "whereclause":
#                    print "vor repl: %s" % val 
#                    where_clause = self._replace_sql_where_clause(val)
#                    print "nach repl: %s" % where_clause
                    
            else:
                sql += "null"
            i += 1
        
        if update:
            sql += " where id=%s" % id
        else:
            sql += ");"
        
        # now try select statement
        cursor = db.cursor()
        if sel_fields or where_clause:
            filter_sql = self.get_filter_select(sel_fields, where_clause)
            
            try:
                cursor.execute(filter_sql)
            except Exception, e:
                try:
                    self.log("DEBUG: XMailFilterObject.save: try db.rollback()")
                    db.rollback()
                    self.log("DEBUG: XMailFilterObject.save: try db.close()")
                    db.close()
                except Exception, e2:
                    self.log("DEBUG: XMailFilterObject.save: db.rollback() db.close()\nException %s" % str(e2) ) 
                    pass  
                self.log("DEBUG: XMailFilterObject.save: try cursor.execute(filter_sql)\nException %s" % str(e) ) 
                raise Warning(filter_sql,e)
            
        cursor.execute(sql)
        db.commit()
        db.close()
        return True

    def log (self, message):
        f = open('/opt/trac/projects/Legato/log/xmailplugin.log', 'r+')
        f.seek(0,2)
        f.write('%s\n' % message)
        f.close()