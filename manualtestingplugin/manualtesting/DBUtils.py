# ManualTesting.DBUtils

from trac.core import *

class DBUtils:
    def __init__(self, component):
        self.env = component.env
        self.log = component.log

    def getData(self, cursor):
        data = [{'name' : 'default', 'value': 'none'}]
        columns = ('name', 'value')
        sql = "SELECT * FROM system"
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            row = dict(zip(columns, row))
            data.append(row)
        return data