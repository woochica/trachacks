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
        suites = self.dbUtils.get_suites(cursor)
        req.hdf['manualtesting.suites'] = suites
        return 'testing.cs', None