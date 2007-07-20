# ManualTesting.ManualTestingAPI

import time
from trac.core import *
from manualtesting.DBUtils import *

class ManualTestingAPI:
    def __init__(self, component):
        self.env = component.env
        self.log = component.log
        self.dbUtils = DBUtils(self)

    # Main request processing function

    def renderUI(self, req, cursor):
        myData = self.dbUtils.getData(cursor)
        req.hdf['data'] = myData
        return 'testing.cs', None