# ManualTesting.DBUtils

from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner

class DBUtils:
    def __init__(self, component):
        self.env = component.env
        self.log = component.log

    def get_suites(self, cursor):
        rows = []
        columns = ('id','title','description','component','deleted','user')
        sql = "SELECT * FROM mtp_suites"
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            rows.append(row)
        return rows

    def get_suite(self, cursor, suite_id):
        columns = ('id','title','description','component','deleted','user')
        sql = "SELECT * FROM mtp_suites WHERE id = %s" % suite_id
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def add_suite(self,cursor,new_user,new_title,new_component,new_description,new_time):
        sql = "INSERT INTO mtp_suites (title,component,description,deleted,user) VALUES ('%s','%s','%s',%s,'%s')" % (new_title,new_component,new_description,0,new_user)
        self.log.debug(sql)
        # ToDo: values in SQL statement must be escaped.
        cursor.execute(sql)

    def get_plans(self, req, cursor, suite_id):
        rows = []
        columns = ('id','title','description')
        sql = "SELECT id, title, description FROM mtp_plans WHERE suite_id = %s" % suite_id
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_html(row['description'], self.env, req)
            rows.append(row)
        return rows

    def add_plan(self,cursor,suite_id,new_user,new_title,new_priority,new_description,new_time):
        sql = "INSERT INTO mtp_plans (suite_id,cDate,mDate,title,priority,description,user) VALUES (%s,%s,%s,'%s','%s','%s','%s')" % (suite_id,1,1,new_title,new_priority,new_description,new_user)
        self.log.debug(sql)
        # ToDo: values in SQL statement must be escaped.
        cursor.execute(sql)

    def get_tracComponents(self, cursor):
        rows = []
        columns = ('name','owner','default')
        sql = "SELECT * FROM component"
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            rows.append(row)
        return rows

    def get_tracVersions(self, cursor):
        rows = []
        columns = ('name','time','default')
        sql = "SELECT * FROM version"
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            rows.append(row)
        return rows

    def get_tracPriorities(self, cursor):
        rows = []
        columns = ('name','value')
        sql = "SELECT name,value FROM enum WHERE type = 'priority'"
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            rows.append(row)
        return rows