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