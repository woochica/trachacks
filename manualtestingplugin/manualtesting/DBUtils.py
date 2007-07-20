# ManualTesting.DBUtils

from trac.core import *

class DBUtils:
    def __init__(self, component):
        self.env = component.env
        self.log = component.log

    def get_suites(self, cursor):
        rows = []
        columns = ('id','title','description','component','deleted','user')
        # INSERT INTO mtp_suites (title, description, component, deleted, user) VALUES ('Search suite','Searching test plans','Search',0,'radams');
        sql = "SELECT * FROM mtp_suites"
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            rows.append(row)
        return rows